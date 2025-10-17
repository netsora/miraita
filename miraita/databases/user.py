from datetime import datetime
from sqlalchemy import String, DateTime, func
from entari_plugin_database import Base, Mapped, mapped_column


class User(Base):
    __bind_key__ = "miraita"
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class Bind(Base):
    __bind_key__ = "miraita"
    __tablename__ = "user"

    platform: Mapped[str] = mapped_column(String(32), primary_key=True)
    platform_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    bind_id: Mapped[int]
    original_id: Mapped[int]
