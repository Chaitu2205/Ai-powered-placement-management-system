from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)


class SkillRead(ORMBase):
    id: int
    name: str
    category: Optional[str]
