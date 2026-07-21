from services.match_history import MatchHistory

class Grind:
    def __init__(self, grind_id, title, start_date, start_rank, current_rank, puuid, platform):
        self.grind_id = grind_id
        self.title = title
        self.start_date = start_date
        self.start_rank = start_rank
        self.current_rank = current_rank
        self.puuid = puuid
        self.platform = platform
        self.match_history = MatchHistory(grind_id)
        self.summoner_name = ""