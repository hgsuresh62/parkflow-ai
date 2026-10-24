"""ParkFlow AI — Reservation Model"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.enums import ReservationStatus


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reservation_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    parking_slot_id: Mapped[int] = mapped_column(Integer, ForeignKey("parking_slots.id"), nullable=False)
    user_session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(Enum(ReservationStatus), default=ReservationStatus.active)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    parking_slot: Mapped["ParkingSlot"] = relationship("ParkingSlot", back_populates="reservations")

    def __repr__(self) -> str:
        return f"<Reservation {self.reservation_code} [{self.status}]>"
