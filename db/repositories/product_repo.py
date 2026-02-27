from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.product import Product
from db.models.category import Category


async def get_categories(session: AsyncSession) -> list[Category]:
    result = await session.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


async def get_products_by_category(session: AsyncSession, category_id: int) -> list[Product]:
    result = await session.execute(
        select(Product)
        .where(Product.category_id == category_id, Product.is_available == True)  # noqa: E712
        .order_by(Product.name)
    )
    return list(result.scalars().all())


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    return await session.get(Product, product_id)


async def get_all_products(session: AsyncSession) -> list[Product]:
    result = await session.execute(
        select(Product).order_by(Product.name)
    )
    return list(result.scalars().all())
