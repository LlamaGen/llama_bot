from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import Messages
from app.database.responses import Responses
from app.database.session_manager import SessionManager
from app.logger import get_logger

logger = get_logger(__name__)


async def save_support_message(message: str, message_id: int, chat_id: int, date: datetime) -> int:
    logger.info(f"Save message {message_id} from {chat_id}")
    session_maker = SessionManager().get_session_maker()
    async with session_maker() as session:
        message = Messages(message_id=message_id, chat_id=chat_id, text=message, date=date)
        session.add(message)
        await session.commit()
    return message.id


async def get_chat_id_by_message(text: str, date: datetime) -> tuple[int, int] | None:
    logger.info(f"Get chat id by message {text} at {date}")
    session_maker = SessionManager().get_session_maker()
    date = date.replace(tzinfo=None)
    async with session_maker() as session:
        query = await session.execute(
            select(Messages).filter(
                Messages.text == text,
                Messages.date >= date - timedelta(seconds=5),
                Messages.date <= date + timedelta(seconds=5),
            )
        )
        result = query.scalar()
    if result is None:
        return None
    return result.chat_id, result.message_id


async def get_chat_message_from_id(requested_id: int) -> tuple[int, int] | None:
    logger.info(f"Get chat id by message {requested_id}")
    session_maker = SessionManager().get_session_maker()
    async with session_maker() as session:
        query = await session.execute(
            select(Messages).filter(
                Messages.id == requested_id,
            )
        )
        result = query.scalar()
    if result is None:
        return None
    return result.chat_id, result.message_id


async def save_model_response(text: str) -> int:
    session_maker = SessionManager().get_session_maker()
    async with session_maker() as session:
        response = Responses(text=text)
        session.add(response)
        await session.commit()
    return response.id


async def get_response_by_id(response_id: int) -> str:
    session_maker = SessionManager().get_session_maker()
    async with session_maker() as session:
        query = await session.execute(
            select(Responses).filter(
                Responses.id == response_id,
            )
        )
        result = query.scalar()
    if result is None:
        return ""
    return result.text
