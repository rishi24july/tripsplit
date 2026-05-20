from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class GroupCreate(BaseModel):
    name:     str = Field(..., min_length=1, max_length=100)
    password: Optional[str] = None
    currency: str = 'INR'

class GroupOut(BaseModel):
    id:           int
    name:         str
    code:         str
    currency:     str
    has_password: bool = False
    created_at:   datetime
    model_config = {"from_attributes": True}

class MemberCreate(BaseModel):
    name:     str = Field(..., min_length=1, max_length=50)
    password: Optional[str] = None

class MemberOut(BaseModel):
    id:       int
    name:     str
    is_admin: bool
    model_config = {"from_attributes": True}

class ExpenseCreate(BaseModel):
    description:     str   = Field(..., min_length=1, max_length=200)
    amount:          float = Field(..., gt=0)
    paid_by_id:      int
    participant_ids: List[int] = Field(..., min_length=1)
    receipt_image:   Optional[str] = None

class ExpenseUpdate(BaseModel):
    description:     Optional[str]       = None
    amount:          Optional[float]     = None
    paid_by_id:      Optional[int]       = None
    participant_ids: Optional[List[int]] = None
    receipt_image:   Optional[str]       = None
