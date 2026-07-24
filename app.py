import threading

import webview
from flask import Flask, render_template, request, redirect, url_for, jsonify
from waitress import serve

from models.goals.rank_goal import RankedGoal
from services.champion_pool_manager import ChampionPoolManager
from services.goal_manager import GoalManager
from services.grind_manager import GrindManager
from services.rank_progression import RankProgressionManager
from services.riot_api_service import RiotApiService
from services.settings_manager import SettingsManager

DDRAGON_VERSION = "14.23.1" # must be updated to keep champ icons up to date

grind_manager = GrindManager()
settings_manager = SettingsManager()
riot_service = RiotApiService()
pool_manager = ChampionPoolManager()

app = Flask(__name__)


@app.context_processor
def inject_globals():
    theme = settings_manager.get_theme()
    return dict(ddragon_version=DDRAGON_VERSION, theme=theme)

@app.route('/')
def index():
    """landing page with all your grinds."""
    api_key = settings_manager.get_api_key()
    key_status = "invalid"
    key_message = "No API key set"
    
    if api_key:
        is_valid, error = riot_service.validate_api_key()
        if is_valid:
            key_status = "valid"
            key_message = "API key is valid"
        else:
            key_message = error or "Invalid API key"
    
    grinds = grind_manager.get_all_grinds()
    for grind in grinds:
        grind_manager.update_current_rank(grind.grind_id, grind.current_rank)
        total_games, winrate = grind_manager.calculate_winrate(grind.grind_id)
        grind.game_count = total_games
        grind.winrate = winrate
    return render_template("index.html", grinds=grinds, show_navbar=False, 
                           key_status=key_status, key_message=key_message)


@app.route('/grinds/<int:grind_id>/champion_pool')
def champion_pool(grind_id):
    """champion pool page."""
    grind = grind_manager.get_grind_by_id(grind_id)
    if not grind:
        return "Grind not found", 404

    pool_dict = pool_manager.get_pool_by_grind_id_dict(grind_id)

    if not pool_dict:
        pool_manager.create_pool(grind_id)
        pool_dict = pool_manager.get_pool_by_grind_id_dict(grind_id)
    
    return render_template('champion_pool.html', grind=grind, pool=pool_dict)

@app.route('/grinds/<int:grind_id>/champion_pool/data')
def get_pool_json(grind_id):
    """Returns pool data as JSON for AJAX updates."""
    pool_dict = pool_manager.get_pool_by_grind_id_dict(grind_id)
    if not pool_dict:
        pool_manager.create_pool(grind_id)
        pool_dict = pool_manager.get_pool_by_grind_id_dict(grind_id)
    
    if not pool_dict:
        return jsonify(success=False, error="Pool not found"), 404
    
    return jsonify(success=True, champions=pool_dict.get('champions', []))

@app.route('/create_grind', methods=['POST'])
def create_grind():
    """creates a new grind."""
    title = request.form.get('title', '').strip()
    game_name = request.form.get('game_name', '').strip()
    tag_line = request.form.get('tag_line', '').strip()
    platform = request.form.get('region', '').strip()

    if not all([title, game_name, tag_line, platform]):
        return {"success": False, "error": "All fields are required"}, 400

    try:
        riot_data = riot_service.get_account_data(game_name, tag_line, platform)
        summoner_name = f"{game_name}#{tag_line}"

        grind_manager.create_grind(
            title=title,
            summoner_name=summoner_name,
            start_rank=riot_data['rank'],
            puuid=riot_data['puuid'],
            platform=platform
        )
        return {"success": True, "redirect": url_for('index')}

    except Exception as e:
        print(f"Error creating grind: {e}")
        return {"success": False, "error": "Failed to find account or fetch rank. Check your spelling or API key!"}, 400



@app.route('/grind/<int:grind_id>/match_history')
def view_grind(grind_id):
    """match history page."""
    grind = grind_manager.get_grind_by_id(grind_id)
    if not grind:
        return "Grind not found", 404
    total_games, winrate = grind_manager.calculate_winrate(grind_id)
    grind.game_count = total_games
    grind.winrate = winrate
    return render_template('match_history.html', grind=grind)

@app.route('/grind/<int:grind_id>/load_matches', methods=['POST'])
def load_matches(grind_id):
    """loads most recent matches from the api and stores them in the db."""
    grind = grind_manager.get_grind_by_id(grind_id)
    if not grind:
        return "Grind not found", 404

    puuid = grind.puuid
    platform = grind.platform
    start_date = grind.start_date

    latest_match = grind.match_history.get_latest_match_timestamp()

    try:
        if latest_match is None:
            start_time = start_date // 1000
        else:
            start_time = latest_match // 1000

        api_matches = riot_service.get_recent_matches_data(puuid, platform, start_time)

        grind.match_history.sync_api_matches(api_matches)

        progression = RankProgressionManager(grind_id)
        if not progression.has_snapshot_today():
            rank_data = riot_service.get_current_rank(puuid, platform)
            if rank_data['tier'].lower() != 'unranked':
                progression.record_snapshot(rank_data['tier'], rank_data['rank'], rank_data['league_points'])

        goal_manager = GoalManager(grind_id)
        if goal_manager.active_rank_goal and goal_manager.active_rank_goal.target_tier in ("GRANDMASTER", "CHALLENGER"):
            challenger_cutoff, grandmaster_cutoff = riot_service.get_cutoffs(platform)
            cutoff = challenger_cutoff if goal_manager.active_rank_goal.target_tier == "CHALLENGER" else grandmaster_cutoff
            goal_manager.active_rank_goal.target_lp = 2800 + cutoff
            goal_manager.update_goal(goal_manager.active_rank_goal)

        return jsonify(success=True, redirect=url_for('view_grind', grind_id=grind_id))

    except Exception as e:
        print(f"Error loading matches: {e}")
        return jsonify(success=False, error="Failed to load matches from Riot API. Check your API key!"), 500

@app.route('/grind/<int:grind_id>/match/<int:match_id>/add_notes', methods=['POST'])
def add_notes(grind_id, match_id):
    """adds new notes to the matches, stores them in the db."""
    grind = grind_manager.get_grind_by_id(grind_id)
    if not grind:
        return "Grind not found", 404

    notes_content = request.form.get('notes')
    success = grind.match_history.add_notes_to_match(match_id, notes_content)

    if not success:
        return 'Match not found', 404

    return redirect(url_for('view_grind', grind_id=grind_id))

@app.route('/grinds/<int:grind_id>/progression/data')
def progression_data(grind_id):
    grind = grind_manager.get_grind_by_id(grind_id)
    if not grind:
        return jsonify(success=False, error="Grind not found"), 404
    progression = RankProgressionManager(grind_id)
    points = progression.get_progression()
    return jsonify(success=True, points=points)


@app.route('/grinds/<int:grind_id>/progression/record', methods=['POST'])
def record_snapshot(grind_id):
    grind = grind_manager.get_grind_by_id(grind_id)
    if not grind:
        return jsonify(success=False, error="Grind not found"), 404

    progression = RankProgressionManager(grind_id)
    if progression.has_snapshot_today():
        return jsonify(success=False, error="Already recorded today"), 400

    rank_data = riot_service.get_current_rank(grind.puuid, grind.platform)
    if rank_data['tier'].lower() == 'unranked':
        return jsonify(success=False, error="Account is unranked"), 400

    progression.record_snapshot(rank_data['tier'], rank_data['rank'], rank_data['league_points'])
    return jsonify(success=True, message="Rank recorded!")


@app.route('/grinds/<int:grind_id>/goals')
def view_goals(grind_id):
    """goals page."""
    grind = grind_manager.get_grind_by_id(grind_id)
    goal_manager = GoalManager(grind_id)
    progression = RankProgressionManager(grind_id)
    peak = progression.get_peak()
    if goal_manager.active_rank_goal:
        target_tier = goal_manager.active_rank_goal.target_tier
        target_lp = goal_manager.active_rank_goal.target_lp
    else:
        target_tier = None
        target_lp = None
    return render_template('goals.html', goal_manager=goal_manager, grind=grind, peak=peak,
                           target_tier=target_tier, target_lp=target_lp)


@app.route('/grinds/<int:grind_id>/goals/add', methods=['POST'])
def add_goal(grind_id):
    """adds new goal."""
    grind = grind_manager.get_grind_by_id(grind_id)
    if not grind:
        return "Grind not found", 404

    goal_type = request.form.get('goal_type', '').strip()
    description = request.form.get('description', '').strip()

    if not goal_type or not description:
        return "Missing required fields", 400

    if goal_type not in ('per_game', 'long_term'):
        return "Invalid goal type", 400

    goal_manager = GoalManager(grind_id)
    goal_manager.create_goal(goal_type, description)

    return redirect(url_for('view_goals', grind_id=grind_id))


@app.route('/grinds/<int:grind_id>/goals/delete/<int:goal_id>', methods=['POST'])
def delete_goal(grind_id, goal_id):
    """deletes a goal."""
    goal_manager = GoalManager(grind_id)
    goal_manager.delete_goal(goal_id)
    return jsonify(success=True)


@app.route('/grinds/<int:grind_id>/goals/rank/edit', methods=['POST'])
def edit_rank_goal(grind_id):
    grind = grind_manager.get_grind_by_id(grind_id)
    if not grind:
        return "Grind not found", 404

    target_tier = request.form.get('target_tier', '').strip().upper()
    if not target_tier:
        return "Missing tier", 400

    if target_tier in ("GRANDMASTER", "CHALLENGER"):
        platform = grind.platform
        challenger_cutoff, grandmaster_cutoff = riot_service.get_cutoffs(platform)
        cutoff = challenger_cutoff if target_tier == "CHALLENGER" else grandmaster_cutoff
        target_lp = 2800 + cutoff
    else:
        target_lp = RankedGoal.TIER_BASE_LP.get(target_tier, 0)

    goal_manager = GoalManager(grind_id)
    if goal_manager.active_rank_goal:
        goal_manager.active_rank_goal.target_tier = target_tier
        goal_manager.active_rank_goal.target_lp = target_lp
        goal_manager.active_rank_goal.description = f"reach {target_tier}"
        goal_manager.update_goal(goal_manager.active_rank_goal)
    else:
        goal_manager.create_goal('rank', target_tier=target_tier, target_lp=target_lp)

    return redirect(url_for('view_goals', grind_id=grind_id))

@app.route('/grinds/<int:grind_id>/champion_pool/add_champion', methods=['POST'])
def add_champion(grind_id):
    """adds a champion to the champion pool."""
    if request.is_json:
        data = request.get_json()
        pool_id = data.get('pool_id')
        champion_name = data.get('champion_name', '').strip()
    else:
        pool_id = request.form['pool_id']
        champion_name = request.form['champion_name'].strip()

    if champion_name: # only depicts icon from data dragon if name matches champ name from api
        # could format names but on the other hand, user can put custom champ name anyway
        pool_manager.add_champion_to_pool(pool_id, champion_name)
    
    if request.is_json:
        return jsonify(success=True)
    # Redirect straight back to refresh the dashboard and show the new icon!
    return redirect(url_for('champion_pool', grind_id=grind_id))


@app.route('/grinds/<int:grind_id>/champion_pool/add_matchup', methods=['POST'])
def add_matchup(grind_id):
    """adds a matchup to a champion of the champion pool."""
    if request.is_json:
        data = request.get_json()
        pool_champion_id = int(data.get('pool_champion_id', 0)) if data.get('pool_champion_id') else 0
        opponent = data.get('opponent', '').strip()
        todo = data.get('todo', '').strip()
        not_todo = data.get('not_todo', '').strip()
        notes = data.get('notes', '').strip()
    else:
        pool_champion_id = request.form.get('pool_champion_id', type=int)
        opponent = request.form.get('opponent', '').strip()
        todo = request.form.get('todo', '').strip()
        not_todo = request.form.get('not_todo', '').strip()
        notes = request.form.get('notes', '').strip()
    
    if pool_champion_id and opponent:
        pool_manager.add_matchup(pool_champion_id, opponent, todo, not_todo, notes)
    
    if request.is_json:
        return jsonify(success=True)
    return redirect(url_for('champion_pool', grind_id=grind_id))


@app.route('/grinds/<int:grind_id>/champion_pool/delete_champion', methods=['POST'])
def delete_champion(grind_id):
    """deletes a champion from the champion pool including all its match ups."""
    if request.is_json:
        data = request.get_json()
        pool_champion_id = int(data.get('pool_champion_id', 0)) if data.get('pool_champion_id') else 0
    else:
        pool_champion_id = request.form.get('pool_champion_id', type=int)
    
    if pool_champion_id:
        pool_manager.delete_champion(pool_champion_id)
    
    if request.is_json:
        return jsonify(success=True)
    return redirect(url_for('champion_pool', grind_id=grind_id))


@app.route('/grinds/<int:grind_id>/champion_pool/delete_matchup', methods=['POST'])
def delete_matchup(grind_id):
    """deletes a matchup from a champion of the champion pool"""
    if request.is_json:
        data = request.get_json()
        matchup_id = int(data.get('matchup_id', 0)) if data.get('matchup_id') else 0
    else:
        matchup_id = request.form.get('matchup_id', type=int)
    
    if matchup_id:

        pool_manager.delete_matchup(matchup_id)
    
    if request.is_json:
        return jsonify(success=True)
    return redirect(url_for('champion_pool', grind_id=grind_id))


@app.route('/grinds/<int:grind_id>/champion_pool/update_matchup', methods=['POST'])
def update_matchup(grind_id):
    """edit the match up notes for a champion match up."""
    if request.is_json:
        data = request.get_json()
        matchup_id = int(data.get('matchup_id', 0)) if data.get('matchup_id') else 0
        opponent = data.get('opponent', '').strip()
        todo = data.get('todo', '').strip()
        not_todo = data.get('not_todo', '').strip()
        notes = data.get('notes', '').strip()
    else:
        matchup_id = request.form.get('matchup_id', type=int)
        opponent = request.form.get('opponent', '').strip()
        todo = request.form.get('todo', '').strip()
        not_todo = request.form.get('not_todo', '').strip()
        notes = request.form.get('notes', '').strip()

    if matchup_id:
        pool_manager.update_matchup(matchup_id, opponent, todo, not_todo, notes)
    
    if request.is_json:
        return jsonify(success=True)
    return redirect(url_for('champion_pool', grind_id=grind_id))


@app.route('/grinds/<int:grind_id>/champion_pool/update_champion_notes', methods=['POST'])
def update_champion_notes(grind_id):
    """updates the notes for a champion."""
    if request.is_json:
        data = request.get_json()
        pool_champion_id = int(data.get('pool_champion_id', 0))
        notes = data.get('notes', '').strip()
    else:
        pool_champion_id = request.form.get('pool_champion_id', type=int)
        notes = request.form.get('notes', '').strip()

    if pool_champion_id:
        pool_manager.update_champion_notes(pool_champion_id, notes)

    if request.is_json:
        return jsonify(success=True)
    return redirect(url_for('champion_pool', grind_id=grind_id))


# API Key management endpoints
@app.route('/api/key-status')
def api_key_status():
    """validates the existing api key."""
    api_key = settings_manager.get_api_key()
    if not api_key:
        return jsonify(status="invalid", message="No API key set")
    
    is_valid, error = riot_service.validate_api_key()
    if is_valid:
        return jsonify(status="valid", message="API key is valid")
    else:
        return jsonify(status="invalid", message=error)


@app.route('/api/test-key', methods=['POST'])
def test_api_key():
    """tests the new api key."""
    data = request.get_json() or {}
    api_key = data.get('api_key', '').strip()
    if not api_key:
        return jsonify(success=False, error="API key cannot be empty"), 400
    
    is_valid, error = riot_service.validate_api_key(api_key)
    if is_valid:
        return jsonify(success=True, message="API key is valid!")
    else:
        return jsonify(success=False, error=error)


@app.route('/api/save-key', methods=['POST'])
def save_api_key():
    """stores the new api key."""
    data = request.get_json() or {}
    api_key = data.get('api_key', '').strip()
    if not api_key:
        return jsonify(success=False, error="API key cannot be empty"), 400
    
    # Test the key first
    is_valid, error = riot_service.validate_api_key(api_key)
    if not is_valid:
        return jsonify(success=False, error=error)
    
    settings_manager.set_api_key(api_key)
    return jsonify(success=True, message="API key saved successfully!")


@app.route('/api/theme', methods=['GET'])
def get_theme():
    theme = settings_manager.get_theme()
    return jsonify(theme=theme)


@app.route('/api/theme', methods=['POST'])
def set_theme():
    data = request.get_json() or {}
    theme = data.get('theme', '').strip()
    valid_themes = ['summoners-rift', 'spirit-blossom', 'darkin']
    if theme not in valid_themes:
        return jsonify(success=False, error="Invalid theme"), 400
    settings_manager.set_theme(theme)
    return jsonify(success=True, theme=theme)

def start_server():
    serve(app, host='127.0.0.1', port=5000)

if __name__ == '__main__':
    threading.Thread(target=start_server, daemon=True).start()

    webview.create_window("My Local App", "http://localhost:5000")
    webview.start()