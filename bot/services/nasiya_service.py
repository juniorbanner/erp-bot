from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from aiogram import Bot
from db.models.user import User
from db.models.transaction import Transaction, TransactionType
from bot.services.notification import send_debt_notification


class NasiyaService:
    def __init__(self, session: AsyncSession, bot: Bot | None = None):
        self.session = session
        self.bot = bot

    async def add_debt(
        self,
        client_id: int,
        amount: float,
        admin_id: int,
        comment: str | None = None,
        txn_type: TransactionType = TransactionType.DEBT_ADDED,
    ) -> Transaction:
        """
        Atomically adds debt to client.
        Uses SELECT FOR UPDATE to prevent race conditions.
        """
        # Lock the row
        result = await self.session.execute(
            select(User).where(User.id == client_id).with_for_update()
        )
        client = result.scalar_one_or_none()
        if not client:
            raise ValueError(f"Клиент с ID {client_id} не найден")
        if not client.is_active:
            raise ValueError("Аккаунт клиента заблокирован")

        balance_before = float(client.nasiya_balance)
        balance_after = balance_before + amount

        # Prevent balance going below zero on repayment
        if balance_after < 0 and amount < 0:
            balance_after = 0.0
            amount = -balance_before

        # Write to ledger
        txn = Transaction(
            user_id=client_id,
            amount=amount,
            type=txn_type,
            balance_before=balance_before,
            balance_after=balance_after,
            comment=comment,
            admin_id=admin_id,
        )
        self.session.add(txn)

        # Update user balance
        await self.session.execute(
            update(User).where(User.id == client_id).values(nasiya_balance=balance_after)
        )
        await self.session.flush()

        # Send notification after successful DB write
        if self.bot:
            await send_debt_notification(
                bot=self.bot,
                telegram_id=client_id,
                amount=amount,
                new_balance=balance_after,
                comment=comment,
            )
        return txn

    async def repay_debt(
        self,
        client_id: int,
        amount: float,
        admin_id: int,
        comment: str | None = None,
    ) -> Transaction:
        return await self.add_debt(
            client_id=client_id,
            amount=-abs(amount),
            admin_id=admin_id,
            comment=comment or "Погашение долга",
            txn_type=TransactionType.DEBT_REPAID,
        )
