# LoL Improvement Journal

A League of Legends improvement journal built with Flask to track your ranked climb, analyze match history, maintain champion pools with matchup notes, and set improvement goals.

## Features

- **Grinds** - Create tracked grinding sessions linked to your Riot account (summoner name + tag + region)
- **Match History** - Fetch and store recent matches from Riot API, add personal notes to each game
- **Champion Pool** - Build a champion pool per grind with matchup-specific notes (what to do / what not to do / general notes)
- **Goals** - Set per-game goals (e.g., "≥8 CS/min") and long-term goals (e.g., "Reach Diamond by split end")
- **Riot API Key Management** - Enter and validate your Riot API key directly from the UI
- **Auto-setup** - Database and tables are created automatically on first run

## Screenshots

| Home / Grinds | Match History |
|---------------|---------------|
| ![Grinds](screenshots/Screenshot%202026-07-21%20103741.png) | ![Match History](screenshots/Screenshot%202026-07-21%20104016.png) |

| Champion Pool | Goals |
|---------------|-------|
| ![Champion Pool](screenshots/Screenshot%202026-07-21%20104506.png) | ![Goals](screenshots/Screenshot%202026-07-21%20104647.png) |

## Quick Start

### Prerequisites
- Python 3.10+
- A [Riot Developer API Key](https://developer.riotgames.com/) (required for match history & rank fetching)

### Installation

```bash
# Clone the repo
git clone https://github.com/ReinhardtDev/league-improvement-journal
cd LeagueImprovementJournal

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
python app.py
```

The app starts at `http://127.0.0.1:5000`. On first run, the SQLite database (`lol_journal.db`) is created automatically.

### Setting Up Your Riot API Key

1. Get an API key from the [Riot Developer Portal](https://developer.riotgames.com/)
2. Open the app in your browser
3. Click the API key indicator in the navbar (shows "Invalid" initially)
4. Enter your key and click **Test & Save**

Once validated, the app can fetch your match history and current rank automatically when you create a grind.

## Project Structure

```
FlaskProject/
├── app.py                    # Flask app entry point
├── lol_journal.db           # SQLite database (auto-created)
├── requirements.txt         # Python dependencies
├── .gitignore
├── README.md
├── screenshots/
├── models/
│   ├── champion.py
│   ├── champion_pool.py
│   ├── grind.py
│   ├── match.py
│   ├── match_up.py
│   ├── goal.py
│   └── goals/
│       ├── long_term_goal.py
│       ├── per_game_goal.py
│       └── rank_goal.py
├── services/                # Business logic
│   ├── champion_pool_manager.py
│   ├── database_service.py
│   ├── goal_manager.py
│   ├── grind_manager.py
│   ├── match_history.py
│   ├── riot_api_service.py
│   └── settings_manager.py
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── match_history.html
    ├── champion_pool.html
    ├── goals.html
    ├── create_grind.html
    └── nav_header.html
```

## Dependencies

Main dependencies (see `requirements.txt` for full list):
- Flask
- SQLAlchemy
- requests (for Riot API)
- python-dotenv (optional, for .env support)

## Riot API Key Notes

- **Development API Key** - Expires every 24h, but easy to get for testing the app
- **Personal API Key** - Requires application, for personal use
- The app validates keys on save and shows status in the navbar
- Data Dragon version (`DDRAGON_VERSION` in `app.py`) must be updated periodically for current champion icons

## Database

SQLite database (`lol_journal.db`) is created automatically on first run. Tables include:
- `grinds` - Grind sessions with summoner info
- `matches` - Match history per grind
- `champion_pools` / `pool_champions` / `matchups` - Champion pool data
- `goals` / `per_game_goals` / `long_term_goals` - Goal tracking
- `settings` - API key storage

## License

MIT License - feel free to use and modify for your own climb!