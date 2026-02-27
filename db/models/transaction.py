import datetime
import enum
from sqlalchemy import Text, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
from db.base import Base


class TransactionType(str, enum.Enum):
    DEBT_ADDED = "debt_added"
    DEBT_REPAID = "debt_repaid"
    ORDER_NASIYA = "order_nasiya"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(15, 2))  # positive = debt, negative = repayment
    type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType))
    balance_before: Mapped[float] = mapped_column(Numeric(15, 2))
    balance_after: Mapped[float] = mapped_column(Numeric(15, 2))
    comment: Mapped[str | None] = mapped_column(Text)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="transactions")  # noqa: F821
    admin: Mapped["User | None"] = relationship("User", foreign_keys=[admin_id])  # noqa: F821
