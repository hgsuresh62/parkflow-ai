"""ParkFlow AI — SensorEvent Model"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.enums import EventSource, SlotStatus


class SensorEvent(Base):
    __tablename__ = "sensor_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sensor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sensors.id"))
    parking_slot_id: Mapped[int] = mapped_column(Integer, ForeignKey("parking_slots.id"), nullable=False)
    raw_distance_cm: Mapped[Optional[float]] = mapped_column(Float)
    occupancy_state: Mapped[SlotStatus] = mapped_column(Enum(SlotStatus), nullable=False)
    source: Mapped[EventSource] = mapped_column(Enum(EventSource), default=EventSource.simulator)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    sensor: Mapped[Optional["Sensor"]] = relationship("Sensor", back_populates="sensor_events")
    parking_slot: Mapped["ParkingSlot"] = relationship("ParkingSlot", back_populates="sensor_events")

    def __repr__(self) -> str:
        return f"<SensorEvent slot={self.parking_slot_id} state={self.occupancy_state}>"
