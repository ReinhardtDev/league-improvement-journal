from datetime import date, datetime, timedelta

from services.database_service import db
from models.goals.rank_goal import RankedGoal


class RankProgressionManager:
    def __init__(self, grind_id):
        self.grind_id = grind_id

    def has_snapshot_today(self):
        """returns whether a rank has already been stored for the day, there should only be one per day."""
        today = date.today().isoformat()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM rank_progression WHERE grind_id = ? AND date = ?",
                (self.grind_id, today)
            )
            return cursor.fetchone() is not None

    def record_snapshot(self, tier, division, lp):
        """records the current rank of a grind."""
        rank_value = RankedGoal.calculate_total_lp(tier, division, lp)
        today = date.today().isoformat()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO rank_progression (grind_id, date, rank) VALUES (?, ?, ?)",
                (self.grind_id, today, rank_value)
            )
            conn.commit()

    def get_progression(self):
        """returns the rank history of a grind."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT date, rank FROM rank_progression WHERE grind_id = ? ORDER BY date ASC, id ASC",
                (self.grind_id,)
            )
            rows = cursor.fetchall()
            points = []
            for row in rows:
                tier, division, lp = RankedGoal.calculate_rank(row['rank'])
                points.append({
                    "date": row['date'],
                    "rank_value": row['rank'],
                    "tier": tier,
                    "division": division,
                    "lp": lp,
                })
            return points

    def get_peak(self):
        """gets the peak rank value of a grind."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MAX(rank) FROM rank_progression WHERE grind_id = ?",
                (self.grind_id,)
            )
            row = cursor.fetchone()
            peak = row[0]
            if peak is None:
                return None
            tier, division, lp = RankedGoal.calculate_rank(peak)
            return {
                "rank_value": peak,
                "tier": tier,
                "division": division,
                "lp": lp,
            }
