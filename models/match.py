
class Match:
    def __init__(self, match_id, match_history_id, date, result, champion, opponent, cs, match_length, kills, deaths, assists, notes):
        self.match_id = match_id
        self.match_history_id = match_history_id
        self.result = result
        self.date = date
        self.champion = champion
        self.opponent = opponent
        self.cs = cs
        self.match_length = match_length
        self.kills = kills
        self.deaths = deaths
        self.assists = assists
        self.notes = notes

    def get_kda(self):
        try:
            kills = int(self.kills)
            deaths = int(self.deaths)
            assists = int(self.assists)


            if deaths == 0:
                return kills + assists
            return round((kills + assists) / deaths, 2)
        except (ValueError, TypeError):
            return 0.0

    def get_cspm(self):
        try:
            cs = int(self.cs)

            minutes_str, seconds_str = self.match_length.split(':')

            minutes = float(minutes_str)
            seconds = float(seconds_str)

            total_minutes = minutes + (seconds / 60.0)

            if total_minutes == 0:
                return 0.0

            return round(cs / total_minutes, 1)

        except (ValueError, AttributeError, TypeError, ZeroDivisionError):
            return 0.0

    def update_notes(self, notes):
        self.notes = notes