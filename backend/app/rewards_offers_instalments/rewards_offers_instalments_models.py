"""
Rewards, offers, and instalments models.

Note: These are re-exports from app.models with the same structure.
The domain module uses the base models directly.
"""
from app.models.instalment_plan import InstalmentPlan
from app.models.offer import Offer
from app.models.rewards_programme import RewardsProgramme

__all__ = ["Offer", "RewardsProgramme", "InstalmentPlan"]
