from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot

from db.base import get_session
from db.models.order import Order, OrderItem, OrderStatus, PaymentType, DeliveryType
from db.models.product import Product
from db.models.user import User
from db.repositories.user_repo import get_user
from bot.config import settings
from bot.services.notification import send_order_receipt
from api.deps import get_current_twa_user

router = APIRouter(prefix="/orders", tags=["orders"])


class CartItem(BaseModel):
    product_id: int
    quantity: int


class CreateOrderRequest(BaseModel):
    items: list[CartItem]
    payment_type: str = "cash"
    delivery_type: str = "pickup"
    delivery_address: str | None = None
    note: str | None = None


@router.post("/")
async def create_order(
    body: CreateOrderRequest,
    twa_user: dict = Depends(get_current_twa_user),
    session: AsyncSession = Depends(get_session),
):
    user_id = twa_user["id"]
    user = await get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please start the bot first.")

    if not body.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Validate products and calculate total
    total = 0.0
    order_items = []
    for cart_item in body.items:
        product = await session.get(Product, cart_item.product_id)
        if not product or not product.is_available:
            raise HTTPException(
                status_code=400,
                detail=f"Product {cart_item.product_id} not available"
            )
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}"
            )
        subtotal = float(product.price) * cart_item.quantity
        total += subtotal
        order_items.append((product, cart_item.quantity, float(product.price)))

    try:
        payment_type = PaymentType(body.payment_type)
    except ValueError:
        payment_type = PaymentType.CASH

    # Create order
    order = Order(
        user_id=user_id,
        status=OrderStatus.PENDING,
        payment_type=payment_type,
        delivery_type=DeliveryType(body.delivery_type) if body.delivery_type in [e.value for e in DeliveryType] else DeliveryType.PICKUP,
        total_amount=total,
        delivery_address=body.delivery_address,
        note=body.note,
    )
    session.add(order)
    await session.flush()

    for product, qty, unit_price in order_items:
        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=unit_price,
        )
        session.add(item)
        # Decrease stock
        product.stock -= qty

    # If nasiya payment, update debt
    if payment_type == PaymentType.NASIYA:
        from bot.services.nasiya_service import NasiyaService
        from db.models.transaction import TransactionType
        bot = Bot(token=settings.BOT_TOKEN)
        service = NasiyaService(session, bot)
        await service.add_debt(
            client_id=user_id,
            amount=total,
            admin_id=user_id,  # self-service via web app
            comment=f"Заказ #{order.id}",
            txn_type=TransactionType.ORDER_NASIYA,
        )
        await bot.session.close()

    await session.flush()

    # Send receipt
    try:
        bot = Bot(token=settings.BOT_TOKEN)
        # Load items for receipt
        result = await session.execute(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        order.items = list(result.scalars().all())
        # Load product names
        for oi in order.items:
            oi.product = await session.get(Product, oi.product_id)
        await send_order_receipt(bot, user_id, order)
        await bot.session.close()
    except Exception:
        pass  # Don't fail order if notification fails

    await session.commit()

    return {
        "order_id": order.id,
        "total": total,
        "status": order.status.value,
        "message": "Заказ принят! Чек отправлен в бот.",
    }
