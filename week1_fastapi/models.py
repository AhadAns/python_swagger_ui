from pydantic import Field, BaseModel
from typing import Optional

class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=30)
    email: str = Field(..., description="User's email")
    age: Optional[int] = Field(None, ge=0, le=100)

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int]

class UpdateUserResponse(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=30)
    email: Optional[str] = Field(None)
    age: Optional[int] = Field(None, ge=0, le=100)

class BusinessException(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code


class TableInfo(BaseModel):
    table_name: str
    table_kind: str

class TableListResponse(BaseModel):
    tables: list[TableInfo]
    count: int
    database: str

class QueryResponse(BaseModel):
    table: str
    row_count: int
    columns: list[str]
    sample_rows: list[dict]