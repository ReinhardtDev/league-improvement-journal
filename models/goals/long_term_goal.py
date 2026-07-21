from models.goal import Goal

class LongTermGoal(Goal):
    def __init__(self, goal_id, grind_id, goal_type, description):
        super().__init__(goal_id, grind_id, goal_type, description)