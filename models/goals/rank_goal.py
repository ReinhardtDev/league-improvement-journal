from models.goal import Goal

class RankedGoal(Goal):

    TIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]

    TIER_BASE_LP = {
        "IRON": 0,
        "BRONZE": 400,
        "SILVER": 800,
        "GOLD": 1200,
        "PLATINUM": 1600,
        "EMERALD": 2000,
        "DIAMOND": 2400,
        "MASTER": 2800,
        "GRANDMASTER": 2800,
        "CHALLENGER": 2800
    }

    DIVISION_MODIFIER = {
        "IV": 0,
        "III": 100,
        "II": 200,
        "I": 300
    }

    def __init__(self, goal_id, grind_id, goal_type, target_tier, target_lp=None):
        self.target_tier = target_tier.upper() if target_tier else None
        if target_lp is not None:
            self.target_lp = target_lp
        else:
            self.target_lp = self.TIER_BASE_LP.get(self.target_tier, 0) if self.target_tier else 0
        description = f"reach {self.target_tier}" if self.target_tier else ""

        super().__init__(goal_id, grind_id, goal_type, description)
        self.goal_id = goal_id

    @classmethod
    def calculate_total_lp(cls, tier, division, lp):
        tier = tier.upper()
        base_lp = cls.TIER_BASE_LP.get(tier, 0)

        if tier in ["MASTER", "GRANDMASTER", "CHALLENGER"]:
            return base_lp + lp

        division_mod = cls.DIVISION_MODIFIER.get(division, 0)
        return base_lp + division_mod + lp

    @classmethod
    def calculate_rank(cls, total_lp):
        if total_lp >= 2800:
            return "MASTER", "I", (total_lp - 2800)

        current_tier = "IRON"
        sorted_tiers = sorted(cls.TIER_BASE_LP.items(), key=lambda item: item[1], reverse=True)

        for tier, base in sorted_tiers:
            if total_lp >= base:
                current_tier = tier
                break

        remainder = total_lp - cls.TIER_BASE_LP[current_tier]

        current_division = "IV"
        sorted_divisions = sorted(cls.DIVISION_MODIFIER.items(), key=lambda item: item[1], reverse=True)

        for division, mod in sorted_divisions:
            if remainder >= mod:
                current_division = division
                break

        final_lp = remainder - cls.DIVISION_MODIFIER[current_division]

        return current_tier, current_division, final_lp
