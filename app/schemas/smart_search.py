from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PositionEnum(str, Enum):
    all_positions = "All Positions"
    attacking_midfield = "Attacking Midfield"
    central_midfield = "Central Midfield"
    centre_back = "Centre-Back"
    centre_forward = "Centre-Forward"
    defensive_midfield = "Defensive Midfield"
    left_winger = "Left Winger"
    left_back = "Left-Back"
    right_back = "Right-Back"
    right_winger = "Right Winger"


class SmartSearchFields(BaseModel):
    name: Optional[str] = Field(None, description="Player name")
    minimum_age: Optional[int] = Field(None, description="Minimum age")
    maximum_age: Optional[int] = Field(None, description="Maximum age")
    current_club: Optional[str] = Field(None, description="Current club name")
    citizenship: Optional[str] = Field(None, description="Player citizenship")
    min_market_value: Optional[int] = Field(None, description="Minimum market value")
    max_market_value: Optional[int] = Field(None, description="Maximum market value")
    position: PositionEnum = Field(PositionEnum.all_positions, description="Player position")
    advise: Optional[str] = Field(None, description="Advise for other good searches")
