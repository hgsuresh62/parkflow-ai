"""ParkFlow AI — RouteRecord Model"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base


class RouteRecord(Base):
    __tablename__ = "route_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    route_uid: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    session_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("parking_sessions.id"))
    source_node: Mapped[str] = mapped_column(String(50), nullable=False)
    destination_node: Mapped[str] = mapped_column(String(50), nullable=False)
    destination_slot_code: Mapped[Optional[str]] = mapped_column(String(20))
    path_nodes: Mapped[Optional[list]] = mapped_column(JSON)  # Ordered list of node IDs
    path_edges: Mapped[Optional[list]] = mapped_column(JSON)  # Edge metadata
    instructions: Mapped[Optional[list]] = mapped_column(JSON)  # Turn-by-turn instructions
    distance_m: Mapped[Optional[float]] = mapped_column(Float)
    estimated_time_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    route_cost: Mapped[Optional[float]] = mapped_column(Float)
    is_valid: Mapped[bool] = mapped_column(default=True)
    invalidated_reason: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    session: Mapped[Optional["ParkingSession"]] = relationship("ParkingSession", back_populates="route_records")

    def __repr__(self) -> str:
        return f"<RouteRecord {self.route_uid} {self.source_node}→{self.destination_node}>"
