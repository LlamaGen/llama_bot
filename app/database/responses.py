from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Responses(Base):  # type: ignore
    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column(index=True)
