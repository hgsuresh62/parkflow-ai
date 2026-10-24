"""ParkFlow AI — Floor Model"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Floor(Base):
    __tablename__ = "floors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    floor_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    layout_config: Mapped[Optional[dict]] = mapped_column(JSON)
    total_slots: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    parking_slots: Mapped[List["ParkingSlot"]] = relationship("ParkingSlot", back_populates="floor", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Floor {self.floor_number}: {self.name}>"
