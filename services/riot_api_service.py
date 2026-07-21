# riot_api.py
from datetime import datetime
import requests
from services.settings_manager import SettingsManager


class RiotApiService:
    def __init__(self):
        pass

    def _get_headers(self):
        """headers for the url"""
        api_key = SettingsManager.get_api_key()
        return {"X-Riot-Token": api_key}

    def _get_regional_routing(self, platform: str) -> str:
        """Helper method to map platform to regional endpoints."""
        if platform in ['na1', 'br1', 'la1', 'la2']:
            return 'americas'
        if platform in ['euw1', 'eun1', 'tr1', 'ru']:
            return 'europe'
        return 'asia'

    def validate_api_key(self, api_key: str = None) -> tuple:
        """Test if an API key is valid by making a lightweight request to Riot.
        Returns (is_valid: bool, error_message: str | None)"""
        import requests
        headers = {"X-Riot-Token": api_key} if api_key else self._get_headers()
        try:
            resp = requests.get("https://euw1.api.riotgames.com/lol/status/v4/platform-data", headers=headers, timeout=10)
            if resp.status_code == 200:
                return True, None
            elif resp.status_code in (401, 403):
                return False, "Invalid or expired API key"
            else:
                return False, f"Unexpected response: {resp.status_code}"
        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"

    def get_account_data(self, game_name: str, tag_line: str, platform: str) -> dict:
        """Fetches the PUUID and current Ranked Solo/Duo rank from Riot."""
        regional = self._get_regional_routing(platform)

        account_url = f"https://{regional}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        account_resp = requests.get(account_url, headers=self._get_headers())
        account_resp.raise_for_status()  # Raises an error if the request failed (e.g., 404 Not Found)
        puuid = account_resp.json()['puuid']

        league_url = f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
        league_resp = requests.get(league_url, headers=self._get_headers()).json()

        rank_str = "Unranked"
        for entry in league_resp:
            if entry['queueType'] == 'RANKED_SOLO_5x5':
                rank_str = f"{entry['tier']} {entry['rank']} ({entry['leaguePoints']} LP)"
                break

        return {
            "puuid": puuid,
            "title": f"{game_name}#{tag_line}",
            "rank": rank_str
        }

    def get_current_rank(self, puuid: str, platform: str) -> dict:
        """returns the current rank as tier rank lp (e.g. Diamond IV 45 lp)."""
        league_url = f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
        league_resp = requests.get(league_url, headers=self._get_headers()).json()

        tier = "unranked"
        rank = "1"
        league_points = "0"

        for entry in league_resp:
            if entry['queueType'] == 'RANKED_SOLO_5x5':
                tier = entry['tier']
                rank = entry['rank']
                league_points = entry['leaguePoints']

        return {
            "tier": tier,
            "rank": rank,
            "league_points": league_points
        }

    def get_recent_matches_data(self, puuid: str, platform: str, last_match_time: int = None, limit: int = 20) -> list:
        """returns the most recent matches as a list of dicts."""
        regional = self._get_regional_routing(platform)
        headers = self._get_headers()

        match_list_url = f"https://{regional}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count={limit}"
        if last_match_time:
            match_list_url += f"&startTime={int(last_match_time + 1)}"

        match_ids = requests.get(match_list_url, headers=headers).json()

        parsed_matches = []

        for match_id in match_ids:
            detail_url = f"https://{regional}.api.riotgames.com/lol/match/v5/matches/{match_id}"
            match_data = requests.get(detail_url, headers=headers).json()

            info = match_data['info']

            player_stats = None
            opponent_stats = None
            your_team_id = None
            your_lane = None

            for participant in info['participants']:
                if participant['puuid'] == puuid:
                    player_stats = participant
                    your_team_id = participant['teamId']
                    your_lane = participant['teamPosition']
                    break

            for participant in info['participants']:
                if participant['teamId'] != your_team_id and participant['teamPosition'] == your_lane:
                    opponent_stats = participant
                    break

            if not player_stats:
                continue

            duration_seconds = info['gameDuration']
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            match_length_str = f"{minutes:02d}:{seconds:02d}"

            date = datetime.fromtimestamp((info['gameStartTimestamp'] / 1000.0)).strftime("%B %d, %Y")

            total_cs = player_stats['totalMinionsKilled'] + player_stats['neutralMinionsKilled']

            parsed_match = {
                "date": info['gameStartTimestamp'],
                "result": "Victory" if player_stats['win'] else "Defeat",
                "champion": player_stats['championName'],
                "opponent": opponent_stats['championName'] if opponent_stats else "Unknown",
                "cs": total_cs,
                "match_length": match_length_str,
                "kills": player_stats['kills'],
                "deaths": player_stats['deaths'],
                "assists": player_stats['assists']
            }
            parsed_matches.append(parsed_match)

        return parsed_matches