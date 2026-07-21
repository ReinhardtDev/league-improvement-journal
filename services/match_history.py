from datetime import datetime

from services.database_service import db
from models.match import Match

class MatchHistory:
    def __init__(self, grind_id):
        self.grind_id = grind_id

    def sync_api_matches(self, api_matches_list):
        """loads the most recent matches from the api_matches_list and inserts them into the database."""
        with db.get_connection() as conn:
            cursor = conn.cursor()

            for m in api_matches_list:
                # Simple check: Does this identical scoreline already exist for this grind?
                cursor.execute('''
                               SELECT id
                               FROM matches
                               WHERE grind_id = ?
                                 AND date = ?  
                                 AND champion = ?
                                 AND kills = ?
                                 AND deaths = ?
                                 AND assists = ?
                               ''', (self.grind_id, m['date'], m['champion'], m['kills'], m['deaths'], m['assists']))

                if cursor.fetchone() is not None:
                    continue  # Skip this match, we already imported it!

                # If it's completely new, insert it!
                cursor.execute('''
                               INSERT INTO matches (grind_id, date, result, champion, opponent,
                                                    cs, match_length, kills, deaths, assists, notes)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                               ''', (self.grind_id, m['date'], m['result'], m['champion'], m['opponent'],
                                     m['cs'], m['match_length'], m['kills'], m['deaths'], m['assists']))
            conn.commit()

    def get_all_matches(self):
        """Returns a list of all matches."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM matches WHERE grind_id = ?", (self.grind_id,))
            rows = cursor.fetchall()

            matches = []
            for row in rows:
                match_obj = Match(
                    match_id=row['id'],
                    match_history_id=row['grind_id'],
                    date = datetime.fromtimestamp((row['date'] / 1000.0)).strftime("%B %d, %Y"),
                    result=row['result'],
                    champion=row['champion'],
                    opponent=row['opponent'],
                    cs=row['cs'],
                    match_length=row['match_length'],
                    kills=row['kills'],
                    deaths=row['deaths'],
                    assists=row['assists'],
                    notes=row['notes']
                )
                matches.append(match_obj)
            return matches

    def get_latest_match_timestamp(self):
        """returns the most recent match timestamp so only new matches are imported."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(date) AS date FROM matches WHERE grind_id = ?", (self.grind_id,))
            row = cursor.fetchone()

            return row['date']

    def add_notes_to_match(self, match_id, notes):
        """adds notes to the match."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE matches SET notes = ? WHERE id = ? AND grind_id = ?",
                (notes, match_id, self.grind_id)
            )
            conn.commit()
            return cursor.rowcount > 0