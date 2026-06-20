"""SQLAlchemy declarative base."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from live_demo_api.db.naming import NAMING_CONVENTION


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
