from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import random, string

import models, schemas
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

# Auto migration - pin column add karo agar nahi hai
def run_migrations():
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE members ADD COLUMN IF NOT EXISTS pin VARCHAR(10)
            """))
            conn.commit()
    except Exception:
        pass

run_migrations()

app = FastAPI(title="TripSplit API", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def gen_code(length=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

# ── Group ────────────────────────────────────────────────────────────────────

@app.post("/api/groups", status_code=201)
def create_group(payload: schemas.GroupCreate, db: Session = Depends(get_db)):
    code = gen_code()
    while db.query(models.Group).filter(models.Group.code == code).first():
        code = gen_code()
    group = models.Group(
        name=payload.name.strip(), code=code,
        password=payload.password.strip() if payload.password else None,
        currency=payload.currency
    )
    db.add(group); db.commit(); db.refresh(group)
    return _group_dict(group)

@app.get("/api/groups/{code}")
def get_group(code: str, db: Session = Depends(get_db)):
    group = _get_group_or_404(code, db)
    return _group_dict(group)

def _group_dict(group):
    return {
        "id": group.id, "name": group.name, "code": group.code,
        "currency": group.currency, "has_password": group.password is not None,
        "created_at": group.created_at.isoformat()
    }

# ── Members ──────────────────────────────────────────────────────────────────

@app.post("/api/groups/{code}/members", status_code=201)
def add_member(code: str, payload: schemas.MemberCreate, db: Session = Depends(get_db)):
    group = _get_group_or_404(code, db)
    if group.password and group.password != (payload.password or ""):
        raise HTTPException(status_code=403, detail="Password galat hai")

    existing = db.query(models.Member).filter(
        models.Member.group_id == group.id,
        models.Member.name == payload.name.strip()
    ).first()
    if existing:
        if existing.pin and payload.pin != existing.pin:
            raise HTTPException(status_code=403, detail="PIN galat hai")
        return _member_dict(existing)

    if not payload.pin:
        raise HTTPException(status_code=400, detail="PIN zaroori hai (4-6 digit)")

    is_first = db.query(models.Member).filter(models.Member.group_id == group.id).count() == 0
    member = models.Member(
        group_id=group.id, name=payload.name.strip(),
        pin=payload.pin, is_admin=is_first
    )
    db.add(member); db.commit(); db.refresh(member)
    return _member_dict(member)

@app.post("/api/groups/{code}/login")
def member_login(code: str, payload: schemas.MemberLogin, db: Session = Depends(get_db)):
    group = _get_group_or_404(code, db)
    member = db.query(models.Member).filter(
        models.Member.group_id == group.id,
        models.Member.name == payload.name.strip()
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Yeh naam group mein nahi hai")
    if member.pin and member.pin != payload.pin:
        raise HTTPException(status_code=403, detail="PIN galat hai")
    return _member_dict(member)

@app.get("/api/groups/{code}/members")
def get_members(code: str, db: Session = Depends(get_db)):
    group = _get_group_or_404(code, db)
    return [_member_dict(m) for m in group.members]

@app.delete("/api/groups/{code}/members/{member_id}")
def remove_member(code: str, member_id: int, admin_id: int, db: Session = Depends(get_db)):
    group = _get_group_or_404(code, db)
    admin = db.query(models.Member).filter(
        models.Member.id == admin_id, models.Member.group_id == group.id,
        models.Member.is_admin == True
    ).first()
    if not admin:
        raise HTTPException(status_code=403, detail="Sirf admin member remove kar sakta hai")
    if admin_id == member_id:
        raise HTTPException(status_code=400, detail="Tum khud ko remove nahi kar sakte")

    member = db.query(models.Member).filter(
        models.Member.id == member_id, models.Member.group_id == group.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member nahi mila")

    paid_count = db.query(models.Expense).filter(models.Expense.paid_by_id == member_id).count()
    if paid_count > 0:
        raise HTTPException(status_code=400, detail=f"Pehle is member ke {paid_count} expense(s) delete karo")

    db.delete(member); db.commit()
    return {"message": f"{member.name} remove ho gaya"}

def _member_dict(m):
    return {"id": m.id, "name": m.name, "is_admin": m.is_admin}

# ── Expenses ─────────────────────────────────────────────────────────────────

@app.post("/api/groups/{code}/expenses", status_code=201)
def add_expense(code: str, payload: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    group = _get_group_or_404(code, db)
    payer = _get_member_or_404(payload.paid_by_id, group.id, db)

    expense = models.Expense(
        group_id=group.id, paid_by_id=payload.paid_by_id,
        description=payload.description.strip(),
        amount=round(payload.amount, 2),
        receipt_image=payload.receipt_image
    )
    db.add(expense); db.flush()
    for mid in set(payload.participant_ids):
        m = db.query(models.Member).filter(
            models.Member.id == mid, models.Member.group_id == group.id).first()
        if m: expense.participants.append(m)

    db.commit(); db.refresh(expense)
    return _expense_dict(expense)

@app.put("/api/groups/{code}/expenses/{expense_id}")
def edit_expense(code: str, expense_id: int, payload: schemas.ExpenseUpdate, db: Session = Depends(get_db)):
    group = _get_group_or_404(code, db)
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id, models.Expense.group_id == group.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense nahi mila")

    if payload.description is not None: expense.description = payload.description.strip()
    if payload.amount is not None:      expense.amount = round(payload.amount, 2)
    if payload.paid_by_id is not None:
        _get_member_or_404(payload.paid_by_id, group.id, db)
        expense.paid_by_id = payload.paid_by_id
    if payload.receipt_image is not None: expense.receipt_image = payload.receipt_image
    if payload.participant_ids is not None:
        expense.participants.clear()
        for mid in set(payload.participant_ids):
            m = db.query(models.Member).filter(
                models.Member.id == mid, models.Member.group_id == group.id).first()
            if m: expense.participants.append(m)

    db.commit(); db.refresh(expense)
    return _expense_dict(expense)

@app.get("/api/groups/{code}/expenses")
def get_expenses(code: str, db: Session = Depends(get_db)):
    group = _get_group_or_404(code, db)
    return [_expense_dict(e) for e in sorted(group.expenses, key=lambda x: x.created_at, reverse=True)]

@app.delete("/api/groups/{code}/expenses/{expense_id}")
def delete_expense(code: str, expense_id: int, db: Session = Depends(get_db)):
    group = _get_group_or_404(code, db)
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id, models.Expense.group_id == group.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense nahi mila")
    db.delete(expense); db.commit()
    return {"message": "Deleted"}

def _expense_dict(exp):
    return {
        "id": exp.id, "description": exp.description, "amount": exp.amount,
        "paid_by_id": exp.paid_by_id, "paid_by_name": exp.paid_by.name,
        "participant_ids":   [p.id   for p in exp.participants],
        "participant_names": [p.name for p in exp.participants],
        "receipt_image": exp.receipt_image,
        "created_at": exp.created_at.isoformat(),
    }

# ── Settlement ───────────────────────────────────────────────────────────────

@app.get("/api/groups/{code}/settlement")
def get_settlement(code: str, db: Session = Depends(get_db)):
    group = _get_group_or_404(code, db)
    paid = {m.name: 0.0 for m in group.members}
    owed = {m.name: 0.0 for m in group.members}

    for exp in group.expenses:
        if not exp.participants: continue
        share = exp.amount / len(exp.participants)
        paid[exp.paid_by.name] += exp.amount
        for p in exp.participants: owed[p.name] += share

    balances = {name: round(paid[name] - owed[name], 2) for name in paid}
    member_totals = [{"name": n, "paid": round(paid[n], 2), "owes": round(owed[n], 2),
                      "net": balances[n]} for n in paid]
    return {
        "group_name": group.name, "currency": group.currency,
        "total_spent": round(sum(e.amount for e in group.expenses), 2),
        "member_totals": member_totals,
        "balances": [{"name": k, "amount": v} for k, v in balances.items()],
        "settlements": _minimize_cash_flow(balances),
    }

def _minimize_cash_flow(balances):
    creditors = sorted([[n, b]  for n, b in balances.items() if b >  0.005], key=lambda x: -x[1])
    debtors   = sorted([[n, -b] for n, b in balances.items() if b < -0.005], key=lambda x: -x[1])
    result = []
    i = j = 0
    while i < len(creditors) and j < len(debtors):
        pay = round(min(creditors[i][1], debtors[j][1]), 2)
        result.append({"from": debtors[j][0], "to": creditors[i][0], "amount": pay})
        creditors[i][1] = round(creditors[i][1] - pay, 2)
        debtors[j][1]   = round(debtors[j][1]   - pay, 2)
        if creditors[i][1] < 0.005: i += 1
        if debtors[j][1]   < 0.005: j += 1
    return result

# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_group_or_404(code, db):
    group = db.query(models.Group).filter(models.Group.code == code.upper()).first()
    if not group: raise HTTPException(status_code=404, detail="Group nahi mila")
    return group

def _get_member_or_404(member_id, group_id, db):
    m = db.query(models.Member).filter(
        models.Member.id == member_id, models.Member.group_id == group_id).first()
    if not m: raise HTTPException(status_code=404, detail="Member nahi mila")
    return m

# ── Frontend ─────────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root(): return FileResponse("static/index.html")

@app.get("/{full_path:path}")
def catch_all(full_path: str): return FileResponse("static/index.html")
