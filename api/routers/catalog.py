from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import get_session
from db.repositories.product_repo import get_categories, get_products_by_category, get_all_products

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/categories")
async def list_categories(session: AsyncSession = Depends(get_session)):
    cats = await get_categories(session)
    return [
        {"id": c.id, "name": c.name, "icon": c.icon}
        for c in cats
    ]


@router.get("/products")
async def list_products(
    category_id: int | None = None,
    session: AsyncSession = Depends(get_session),
):
    if category_id:
        products = await get_products_by_category(session, category_id)
    else:
        products = await get_all_products(session)

    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": float(p.price),
            "stock": p.stock,
            "is_available": p.is_available,
            "photo_file_id": p.photo_file_id,
            "category_id": p.category_id,
        }
        for p in products
        if p.is_available
    ]
