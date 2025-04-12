from pydantic import BaseModel
from typing import List


class TeamPlayerBase(BaseModel):
    userid: int
    game_uid: int
    role: str


class TeamBase(BaseModel):
    name: str
    tag: str
    region: str
    ban_status:str
    ban_reason:str
    ban_duration:str



class TeamViewResponse(BaseModel):
    team: TeamBase
    players: List[TeamPlayerBase]

    class Config:
        orm_mode = True