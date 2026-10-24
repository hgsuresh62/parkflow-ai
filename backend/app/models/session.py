"""ParkFlow AI — ParkingSession Model"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.enums import SessionStatus


class ParkingSession(Base):
    __tablename__ = "parking_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_uid: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    selected_slot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("parking_slots.id"))
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.navigating)
    vehicle_id: Mapped[Optional[str]] = mapped_column(String(50))
    user_session_id: Mapped[Optional[str]] = mapped_column(String(100))
    navigation_state: Mapped[Optional[dict]] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    arrived_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    selected_slot: Mapped[Optional["ParkingSlot"]] = relationship("ParkingSlot")
    route_records: Mapped[list] = relationship("RouteRecord", back_populates="session")

    def __repr__(self) -> str:
        return f"<ParkingSession {self.session_uid} [{self.status}]>"
