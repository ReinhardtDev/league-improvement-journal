from models.goal import Goal

class PerGameGoal(Goal):
    def __init__(self, goal_id, grind_id, goal_type, description, reached=False):
        super().__init__(goal_id, grind_id, goal_type, description)
        self.reached = reached