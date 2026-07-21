

class Champion:
    def __init__(self, pool_champion_id, pool_id, champion_name, notes=""):
        self.pool_champion_id = pool_champion_id
        self.pool_id = pool_id
        self.champion_name = champion_name
        self.notes = notes
        self.matchups = []

    def to_dict(self):
        return {
            'pool_champion_id': self.pool_champion_id,
            'pool_id': self.pool_id,
            'champion_name': self.champion_name,
            'notes': self.notes,
            'matchups': [m.to_dict() for m in self.matchups]
        }
