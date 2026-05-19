from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ─── Group ──────────────────────────────────────────────────────────────────
class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class GroupOut(BaseModel):
    id:         int
    name:       str
    code:       str
    created_at: datetime

    model_config = {"from_attributes": True}

# ─── Member ─────────────────────────────────────────────────────────────────
class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class MemberOut(BaseModel):
    id:   int
    name: str

    model_config = {"from_attributes": True}

# ─── Expense ────────────────────────────────────────────────────────────────
class ExpenseCreate(BaseModel):
    description:     str   = Field(..., min_length=1, max_length=200)
    amount:          float = Field(..., gt=0)
    paid_by_id:      int
    participant_ids: List[int] = Field(..., min_length=1)

class ExpenseOut(BaseModel):
    id:                int
    description:       str
    amount:            float
    paid_by_id:        int
    paid_by_name:      str
    participant_ids:   List[int]
    participant_names: List[str]
    created_at:        str

# ─── Settlement ─────────────────────────────────────────────────────────────
class SettlementItem(BaseModel):
    from_name: str
    to_name:   str
    amount:    float

class MemberTotal(BaseModel):
    name:  str
    paid:  float
    owes:  float
    net:   float
