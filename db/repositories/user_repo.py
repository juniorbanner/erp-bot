from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.user import User


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    return await session.get(User, telegram_id)


async def get_user_by_phone(session: AsyncSession, phone: str) -> User | None:
    result = await session.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_or_create_user(session: AsyncSession, telegram_id: int, tg_user) -> User:
    user = await session.get(User, telegram_id)
    if not user:
        user = User(
            id=telegram_id,
            full_name=tg_user.full_name,
            username=tg_user.username,
        )
        session.add(user)
        await session.flush()
    return user


async def search_user(session: AsyncSession, query: str) -> User | None:
    """Search by telegram ID or phone number."""
    query = query.strip()
    if query.isdigit():
        user = await session.get(User, int(query))
        if user:
            return user
    # search by phone
    phone = query.replace("+", "").replace(" ", "").replace("-", "")
    result = await session.execute(
        select(User).where(User.phone.contains(phone))
    )
    return result.scalar_one_or_none()


async def get_all_clients(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User).where(User.is_admin == False, User.is_active == True)  # noqa: E712
    )
    return list(result.scalars().all())


async def get_debtors(session: AsyncSession, min_balance: float = 0.01) -> list[User]:
    result = await session.execute(
        select(User)
        .where(User.nasiya_balance >= min_balance)
        .order_by(User.nasiya_balance.desc())
    )
    return list(result.scalars().all())
