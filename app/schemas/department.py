from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=1, max_length=20)


class DepartmentRead(ORMBase):
    id: int
    name: str
    code: str
