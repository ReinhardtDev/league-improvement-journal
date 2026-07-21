from services.database_service import db
from models.goals.long_term_goal import LongTermGoal
from models.goals.per_game_goal import PerGameGoal
from models.goals.rank_goal import RankedGoal


class GoalManager:
    def __init__(self, grind_id):
        self.grind_id = grind_id
        self.general_goals = []
        self.active_rank_goal = None
        self.load_all_goals()

    def create_goal(self, goal_type, description=None, target_rank=None):
        """creates a goal of a specific type."""
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """INSERT INTO goals (grind_id, goal_type, description, reached, target_lp)
                   VALUES (?, ?, ?, 0, ?)""",
                (self.grind_id, goal_type, description, target_rank)
            )
            conn.commit()

    def load_all_goals(self):
        """adds all the goals from the db to the list of goals."""
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM goals WHERE grind_id = ?", (self.grind_id,))
            rows = cursor.fetchall()

            for row in rows:
                goal_id = row['id']
                grind_id = row['grind_id']
                goal_type = row['goal_type']
                description = row['description']

                if goal_type == 'rank':
                    self.active_rank_goal = RankedGoal(goal_id, grind_id, goal_type, int(row['target_lp']))

                elif goal_type == 'per_game':
                    self.general_goals.append(PerGameGoal(goal_id, grind_id, goal_type, description))  # here put reached in future

                elif goal_type == "long_term":
                    self.general_goals.append(LongTermGoal(goal_id, grind_id, goal_type, description))

    def update_goal(self, goal_object):
        """updates a goal of a specific type (its description or target lp depending on the type)."""
        with db.get_connection() as conn:
            cursor = conn.cursor()

            if isinstance(goal_object, RankedGoal):
                cursor.execute("""
                               UPDATE goals
                               SET target_lp = ?
                               WHERE goal_id = ?
                                 AND grind_id = ?
                               """, (goal_object.target_lp, goal_object.goal_id, self.grind_id))

            elif isinstance(goal_object, PerGameGoal): # here also reached in future
                cursor.execute("""
                               UPDATE goals
                               SET description = ?
                               WHERE goal_id = ? AND grind_id = ?
                               """, (goal_object.description, goal_object.goal_id, self.grind_id))

            elif isinstance(goal_object, LongTermGoal):
                cursor.execute("""
                               UPDATE goals
                               SET description = ?
                               WHERE goal_id = ? AND grind_id = ?
                               """, (goal_object.description, goal_object.goal_id, self.grind_id))

            conn.commit()

    def delete_goal(self, goal_id):
        """deletes a goal."""
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""DELETE FROM goals WHERE goal_id = ? AND grind_id = ?""", (goal_id, self.grind_id))
            conn.commit()

        if self.active_rank_goal and self.active_rank_goal.goal_id == goal_id:
            self.active_rank_goal = None
        else:
            self.general_goals = [g for g in self.general_goals if g.goal_id != goal_id]