"""ParkFlow AI — ParkingSlot Model"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.enums import SlotStatus, SlotType


class ParkingSlot(Base):
    __tablename__ = "parking_slots"
    __table_args__ = (
        Index("ix_slots_floor_status", "floor_id", "status"),
        Index("ix_slots_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slot_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    floor_id: Mapped[int] = mapped_column(Integer, ForeignKey("floors.id"), nullable=False)
    slot_type: Mapped[SlotType] = mapped_column(Enum(SlotType), default=SlotType.standard)
    status: Mapped[SlotStatus] = mapped_column(Enum(SlotStatus), default=SlotStatus.available)
    row_label: Mapped[Optional[str]] = mapped_column(String(10))
    position_x: Mapped[Optional[float]] = mapped_column(Float)  # SVG x coordinate
    position_y: Mapped[Optional[float]] = mapped_column(Float)  # SVG y coordinate
    graph_node: Mapped[Optional[str]] = mapped_column(String(50), index=True)  # Navigation graph node ID
    sensor_id: Mapped[Optional[str]] = mapped_column(String(50))
    last_sensor_update: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_accessible: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    floor: Mapped["Floor"] = relationship("Floor", back_populates="parking_slots")
    sensors: Mapped[List["Sensor"]] = relationship("Sensor", back_populates="parking_slot", lazy="selectin")
    reservations: Mapped[List["Reservation"]] = relationship("Reservation", back_populates="parking_slot")
    sensor_events: Mapped[List["SensorEvent"]] = relationship("SensorEvent", back_populates="parking_slot")

    def __repr__(self) -> str:
        return f"<ParkingSlot {self.slot_code} [{self.status}]>"
