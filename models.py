from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Table, Boolean, Text
from sqlalchemy.orm import relationship
from database import Base
import datetime

expense_participants = Table(
    "expense_participants",
    Base.metadata,
    Column("expense_id", Integer, ForeignKey("expenses.id", ondelete="CASCADE")),
    Column("member_id",  Integer, ForeignKey("members.id",  ondelete="CASCADE")),
)

class Group(Base):
    __tablename__ = "groups"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    code       = Column(String(10), unique=True, index=True, nullable=False)
    password   = Column(String(100), nullable=True)
    currency   = Column(String(10), default='INR')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    members    = relationship("Member", back_populates="group", cascade="all, delete-orphan")
    expenses   = relationship("Expense", back_populates="group", cascade="all, delete-orphan")

class Member(Base):
    __tablename__ = "members"
    id         = Column(Integer, primary_key=True, index=True)
    group_id   = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    name       = Column(String(50), nullable=False)
    pin        = Column(String(10), nullable=True)
    is_admin   = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    group         = relationship("Group", back_populates="members")
    paid_expenses = relationship("Expense", back_populates="paid_by")
    in_expenses   = relationship("Expense", secondary=expense_participants, back_populates="participants")

class Expense(Base):
    __tablename__ = "expenses"
    id            = Column(Integer, primary_key=True, index=True)
    group_id      = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    paid_by_id    = Column(Integer, ForeignKey("members.id"), nullable=False)
    description   = Column(String(200), nullable=False)
    amount        = Column(Float, nullable=False)
    receipt_image = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)
    group        = relationship("Group", back_populates="expenses")
    paid_by      = relationship("Member", back_populates="paid_expenses", foreign_keys=[paid_by_id])
    participants = relationship("Member", secondary=expense_participants, back_populates="in_expenses")
