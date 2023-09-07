from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Messages(Base):  # type: ignore
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(index=True)
    chat_id: Mapped[int] = mapped_column(index=True)
    date: Mapped[datetime] = mapped_column(index=True)
    text: Mapped[str] = mapped_column(index=True)
