from models.grind import Grind
from services.database_service import db
from services.match_history import MatchHistory
from datetime import datetime


class GrindManager:
    def __init__(self):
        pass

    def create_grind(self, title, summoner_name, start_rank, puuid, platform):
        """Creates a new grind with the start date being right now!"""

        start_date = int(datetime.now().timestamp() * 1000)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO grinds (title, summoner_name, start_date, start_rank, current_rank, puuid, platform) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (title, summoner_name, start_date, start_rank, start_rank, puuid, platform)
            )
            conn.commit()
            new_id = cursor.lastrowid

        new_grind = Grind(new_id, title, start_date, start_rank, start_rank, puuid, platform)
        new_grind.summoner_name = summoner_name
        new_grind.match_history = MatchHistory(new_id)
        return new_grind

    def get_grind_by_id(self, grind_id):
        """returns a grind with a specific grind id."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, summoner_name, start_date, start_rank, current_rank, puuid, platform FROM grinds WHERE id = ?", (grind_id,))
            row = cursor.fetchone()

            if row:
                grind = Grind(
                    grind_id=row['id'],
                    title=row['title'],
                    start_date=row['start_date'],
                    start_rank=row['start_rank'],
                    current_rank=row['current_rank'],
                    puuid=row['puuid'],
                    platform=row['platform']
                )
                grind.summoner_name = row['summoner_name']
                return grind
            return None

    def update_current_rank(self, grind_id, current_rank):
        """updates the current rank of a grind."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE grinds 
            SET current_rank = ? 
            WHERE id = ?''', (current_rank, grind_id))
            conn.commit()
            return cursor.rowcount > 0

    def remove_grind(self, grind_id):
        """Removes a grind."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM grinds WHERE id = ?", (grind_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_grinds(self):
        """Returns a list of all grinds."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM grinds")
            rows = cursor.fetchall()

            all_grinds = []
            for row in rows:
                grind = Grind(
                grind_id=row['id'],
                title=row['title'],
                start_date = datetime.fromtimestamp((row['start_date'] / 1000.0)).strftime("%B %d, %Y"),
                start_rank=row['start_rank'],
                current_rank=row['current_rank'],
                puuid=row['puuid'],
                platform=row['platform']
            )
                grind.summoner_name = row['summoner_name']
                grind.match_history = MatchHistory(row['id'])
                all_grinds.append(grind)
            return all_grinds

    def calculate_winrate(self, grind_id):
        """Calculates the winrate and total games of a grind from the matches table."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as total, SUM(CASE WHEN result = 'Victory' THEN 1 ELSE 0 END) as wins FROM matches WHERE grind_id = ?",
                (grind_id,)
            )
            row = cursor.fetchone()
            total = row['total'] if row else 0
            wins = row['wins'] if row else 0

        if total == 0:
            return 0, "0%"
        winrate = round((wins / total) * 100)
        return total, f"{winrate}%"
