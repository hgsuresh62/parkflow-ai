"""ParkFlow AI — SQLAlchemy Models"""
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, Enum, ForeignKey,
    DateTime, JSON, Text, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base


class SlotStatus(str, enum.Enum):
    available = "available"
    occupied = "occupied"
    reserved = "reserved"
    maintenance = "maintenance"
    pending = "pending"


class SlotType(str, enum.Enum):
    standard = "standard"
    accessible = "accessible"
    ev_charging = "ev_charging"
    compact = "compact"
    oversized = "oversized"


class ReservationStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"
    fulfilled = "fulfilled"


class SessionStatus(str, enum.Enum):
    navigating = "navigating"
    arrived = "arrived"
    cancelled = "cancelled"
    completed = "completed"


class SensorStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    error = "error"
    unknown = "unknown"


class EventSource(str, enum.Enum):
    simulator = "simulator"
    thingspeak = "thingspeak"
    mqtt = "mqtt"
    manual = "manual"
    hardware = "hardware"
