
class Matchup:
    def __init__(self, matchup_id, pool_champion_id, opponent, todo="", not_todo="", notes=""):
        self.matchup_id = matchup_id
        self.pool_champ_id = pool_champion_id
        self.opponent = opponent
        self.todo = todo
        self.not_todo = not_todo
        self.notes = notes

    def to_dict(self):
        return {
            'matchup_id': self.matchup_id,
            'pool_champion_id': self.pool_champ_id,
            'opponent': self.opponent,
            'todo': self.todo,
            'not_todo': self.not_todo,
            'notes': self.notes
        }
