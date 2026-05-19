from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import random, string, os

import models, schemas
from database import engine, SessionLocal

# ─── App Setup ──────────────────────────────────────────────────────────────
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="TripSplit API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def gen_code(length=6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))

# ─── Group Endpoints ─────────────────────────────────────────────────────────

@app.post("/api/groups", response_model=schemas.GroupOut, status_code=201)
def create_group(payload: schemas.GroupCreate, db: Session = Depends(get_db)):
    code = gen_code()
    while db.query(models.Group).filter(models.Group.code == code).first():
        code = gen_code()
    group = models.Group(name=payload.name.strip(), code=code)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@app.get("/api/groups/{code}", response_model=schemas.GroupOut)
def get_group(code: str, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.code == code.upper()).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group nahi mila")
    return group


# ─── Member Endpoints ─────────────────────────────────────────────────────────

@app.post("/api/groups/{code}/members", response_model=schemas.MemberOut, status_code=201)
def add_member(code: str, payload: schemas.MemberCreate, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.code == code.upper()).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group nahi mila")

    # Return existing member if name already taken
    existing = db.query(models.Member).filter(
        models.Member.group_id == group.id,
        models.Member.name == payload.name.strip()
    ).first()
    if existing:
        return existing

    member = models.Member(group_id=group.id, name=payload.name.strip())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@app.get("/api/groups/{code}/members", response_model=List[schemas.MemberOut])
def get_members(code: str, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.code == code.upper()).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group nahi mila")
    return group.members


# ─── Expense Endpoints ────────────────────────────────────────────────────────

def _expense_dict(exp: models.Expense) -> dict:
    return {
        "id":                exp.id,
        "description":       exp.description,
        "amount":            exp.amount,
        "paid_by_id":        exp.paid_by_id,
        "paid_by_name":      exp.paid_by.name,
        "participant_ids":   [p.id   for p in exp.participants],
        "participant_names": [p.name for p in exp.participants],
        "created_at":        exp.created_at.isoformat(),
    }


@app.post("/api/groups/{code}/expenses", status_code=201)
def add_expense(code: str, payload: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.code == code.upper()).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group nahi mila")

    payer = db.query(models.Member).filter(
        models.Member.id == payload.paid_by_id,
        models.Member.group_id == group.id
    ).first()
    if not payer:
        raise HTTPException(status_code=404, detail="Payer member nahi mila")

    expense = models.Expense(
        group_id    = group.id,
        paid_by_id  = payload.paid_by_id,
        description = payload.description.strip(),
        amount      = round(payload.amount, 2),
    )
    db.add(expense)
    db.flush()

    for mid in set(payload.participant_ids):
        m = db.query(models.Member).filter(
            models.Member.id == mid,
            models.Member.group_id == group.id
        ).first()
        if m:
            expense.participants.append(m)

    db.commit()
    db.refresh(expense)
    return _expense_dict(expense)


@app.get("/api/groups/{code}/expenses")
def get_expenses(code: str, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.code == code.upper()).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group nahi mila")
    return [_expense_dict(e) for e in sorted(group.expenses, key=lambda x: x.created_at, reverse=True)]


@app.delete("/api/groups/{code}/expenses/{expense_id}")
def delete_expense(code: str, expense_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.code == code.upper()).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group nahi mila")

    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.group_id == group.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense nahi mila")

    db.delete(expense)
    db.commit()
    return {"message": "Expense delete ho gaya"}


# ─── Settlement Endpoint ──────────────────────────────────────────────────────

def _minimize_cash_flow(balances: dict) -> list:
    """Greedy algorithm: minimum number of transactions to settle all debts."""
    creditors = sorted([(n, b) for n, b in balances.items() if b >  0.005], key=lambda x: -x[1])
    debtors   = sorted([(n, -b) for n, b in balances.items() if b < -0.005], key=lambda x: -x[1])

    creditors = [list(x) for x in creditors]
    debtors   = [list(x) for x in debtors]

    result = []
    i = j = 0
    while i < len(creditors) and j < len(debtors):
        cr_name, cr_amt = creditors[i]
        db_name, db_amt = debtors[j]
        pay = round(min(cr_amt, db_amt), 2)
        result.append({"from": db_name, "to": cr_name, "amount": pay})
        creditors[i][1] = round(cr_amt - pay, 2)
        debtors[j][1]   = round(db_amt - pay, 2)
        if creditors[i][1] < 0.005: i += 1
        if debtors[j][1]   < 0.005: j += 1

    return result


@app.get("/api/groups/{code}/settlement")
def get_settlement(code: str, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.code == code.upper()).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group nahi mila")

    members  = group.members
    expenses = group.expenses

    # Per-member: total paid and total owed
    paid = {m.name: 0.0 for m in members}
    owed = {m.name: 0.0 for m in members}

    for exp in expenses:
        if not exp.participants:
            continue
        share = exp.amount / len(exp.participants)
        paid[exp.paid_by.name] += exp.amount
        for p in exp.participants:
            owed[p.name] += share

    # Net balance: positive = others owe this person, negative = this person owes others
    balances = {name: round(paid[name] - owed[name], 2) for name in paid}

    member_totals = [
        {
            "name":  name,
            "paid":  round(paid[name], 2),
            "owes":  round(owed[name], 2),
            "net":   balances[name],
        }
        for name in paid
    ]

    return {
        "group_name":    group.name,
        "total_spent":   round(sum(e.amount for e in expenses), 2),
        "member_totals": member_totals,
        "balances":      [{"name": k, "amount": v} for k, v in balances.items()],
        "settlements":   _minimize_cash_flow(balances),
    }


# ─── Serve Frontend ───────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/{full_path:path}")
def catch_all(full_path: str):
    return FileResponse("static/index.html")
