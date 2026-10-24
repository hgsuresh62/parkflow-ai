"""ParkFlow AI — Sensor Model"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.enums import SensorStatus, EventSource


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sensor_uid: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    sensor_type: Mapped[str] = mapped_column(String(50), default="ultrasonic_hcsr04")
    parking_slot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("parking_slots.id"))
    provider: Mapped[EventSource] = mapped_column(Enum(EventSource), default=EventSource.simulator)
    status: Mapped[SensorStatus] = mapped_column(Enum(SensorStatus), default=SensorStatus.online)
    last_distance_cm: Mapped[Optional[float]] = mapped_column(Float)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    parking_slot: Mapped[Optional["ParkingSlot"]] = relationship("ParkingSlot", back_populates="sensors")
    sensor_events: Mapped[list] = relationship("SensorEvent", back_populates="sensor")

    def __repr__(self) -> str:
        return f"<Sensor {self.sensor_uid} [{self.status}]>"
