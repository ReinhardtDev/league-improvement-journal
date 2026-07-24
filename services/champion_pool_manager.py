from models.champion import Champion
from models.champion_pool import ChampionPool
from models.match_up import Matchup
from services.database_service import db


class ChampionPoolManager:
    def __init__(self):
        pass

    def create_pool(self, grind_id):
        """Creates an empty champion pool for a specific grind."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO champion_pools (grind_id) VALUES (?)",
                (grind_id,)
            )
            conn.commit()
            new_id = cursor.lastrowid

        return ChampionPool(pool_id=new_id, grind_id=grind_id)

    def add_champion_to_pool(self, pool_id, champion_name):
        """Adds a new champion to a specific pool row."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO pool_champions (pool_id, champion, notes) VALUES (?, ?, ?)",
                (pool_id, champion_name, "")
            )
            conn.commit()
            new_id = cursor.lastrowid

        return Champion(pool_champion_id=new_id, pool_id=pool_id, champion_name=champion_name)

    def add_matchup(self, pool_champion_id, opponent, todo="", not_todo="", notes=""):
        """Creates a blank matchup sheet against a specific opponent."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO match_ups (pool_champion_id, opponent, todo, not_todo, notes) VALUES (?, ?, ?, ?, ?)",
                (pool_champion_id, opponent, todo, not_todo, notes)
            )
            conn.commit()
            new_id = cursor.lastrowid

        return Matchup(matchup_id=new_id, pool_champion_id=pool_champion_id, opponent=opponent, todo=todo, not_todo=not_todo, notes=notes)

    def delete_champion(self, pool_champion_id):
        """Deletes a champion and all its matchups."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pool_champions WHERE id = ?", (pool_champion_id,))
            conn.commit()
            return cursor.rowcount > 0

    def delete_matchup(self, matchup_id):
        """Deletes a specific matchup."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM match_ups WHERE id = ?", (matchup_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_matchup(self, matchup_id, opponent, todo, not_todo, notes):
        """Updates a matchup's fields."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE match_ups SET opponent = ?, todo = ?, not_todo = ?, notes = ? WHERE id = ?",
                (opponent, todo, not_todo, notes, matchup_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_champion_notes(self, pool_champion_id, notes):
        """Updates a champion's notes."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE pool_champions SET notes = ? WHERE id = ?",
                (notes, pool_champion_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_pool_by_grind_id(self, grind_id):
        """Fetches the pool, its champions, and all matchups for a given grind."""
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Get the pool row
            cursor.execute("SELECT id FROM champion_pools WHERE grind_id = ?", (grind_id,))
            pool_row = cursor.fetchone()
            if not pool_row:
                return None

            pool = ChampionPool(pool_id=pool_row['id'], grind_id=grind_id)

            # 2. Get all champions in this pool
            cursor.execute("SELECT id, champion, notes FROM pool_champions WHERE pool_id = ?", (pool.pool_id,))
            champ_rows = cursor.fetchall()

            for c_row in champ_rows:
                champ = Champion(
                    pool_champion_id=c_row['id'],
                    pool_id=pool.pool_id,
                    champion_name=c_row['champion'],
                    notes=c_row['notes']
                )

                # 3. Get all matchups for this specific champion
                cursor.execute(
                    "SELECT id, opponent, todo, not_todo, notes FROM match_ups WHERE pool_champion_id = ?",
                    (champ.pool_champion_id,)
                )
                matchup_rows = cursor.fetchall()

                for m_row in matchup_rows:
                    matchup = Matchup(
                        matchup_id=m_row['id'],
                        pool_champion_id=champ.pool_champion_id,
                        opponent=m_row['opponent'],
                        todo=m_row['todo'],
                        not_todo=m_row['not_todo'],
                        notes=m_row['notes']
                    )
                    champ.matchups.append(matchup)

                pool.champions.append(champ)

            return pool

    def get_pool_by_grind_id_dict(self, grind_id):
        """Returns pool data as JSON-serializable dicts for templates."""
        pool = self.get_pool_by_grind_id(grind_id)
        if not pool:
            return None
        return {
            'pool_id': pool.pool_id,
            'grind_id': pool.grind_id,
            'champions': [c.to_dict() for c in pool.champions]
        }
