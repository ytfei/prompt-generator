import uuid
from datetime import UTC, datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class Generation(Base):
    __tablename__ = "generations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[str] = mapped_column(String, index=True)
    selections: Mapped[str] = mapped_column(String)  # JSON
    theme: Mapped[str] = mapped_column(String, default="")
    final_prompt: Mapped[str] = mapped_column(String)
    notes: Mapped[str] = mapped_column(String, default="[]")  # JSON 数组
    warnings: Mapped[str] = mapped_column(String, default="[]")  # JSON 数组
    model: Mapped[str] = mapped_column(String)
    mode: Mapped[str] = mapped_column(String, default="standard")
    favorite: Mapped[int] = mapped_column(Integer, default=0)


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    selections: Mapped[str] = mapped_column(String)  # JSON
    created_at: Mapped[str] = mapped_column(String)
