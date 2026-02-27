"""
Seed script — adds initial categories and demo products to DB.
Run: python seed.py
"""
import asyncio
from db.base import engine, Base, AsyncSessionFactory
from db.models.category import Category
from db.models.product import Product
from db.models.user import User
import os

# Load env
from dotenv import load_dotenv
load_dotenv()


CATEGORIES = [
    {"name": "Хлеб и выпечка", "icon": "🍞"},
    {"name": "Молочные продукты", "icon": "🥛"},
    {"name": "Мясо", "icon": "🥩"},
    {"name": "Овощи и фрукты", "icon": "🥦"},
    {"name": "Бакалея", "icon": "🛒"},
    {"name": "Напитки", "icon": "🥤"},
]

PRODUCTS = [
    # Хлеб
    {"name": "Нон (лепёшка)", "price": 5000, "stock": 50, "category": 0},
    {"name": "Батон белый", "price": 8000, "stock": 30, "category": 0},
    {"name": "Самса (1 шт)", "price": 6000, "stock": 20, "category": 0},
    # Молочные
    {"name": "Молоко 1л", "price": 12000, "stock": 40, "category": 1},
    {"name": "Сметана 200г", "price": 15000, "stock": 25, "category": 1},
    {"name": "Яйцо (10 шт)", "price": 28000, "stock": 60, "category": 1},
    # Мясо
    {"name": "Говядина 1кг", "price": 95000, "stock": 15, "category": 2},
    {"name": "Курица 1кг", "price": 55000, "stock": 20, "category": 2},
    # Овощи
    {"name": "Помидоры 1кг", "price": 10000, "stock": 30, "category": 3},
    {"name": "Картофель 1кг", "price": 8000, "stock": 50, "category": 3},
    {"name": "Лук репчатый 1кг", "price": 5000, "stock": 40, "category": 3},
    # Бакалея
    {"name": "Рис девзира 1кг", "price": 22000, "stock": 30, "category": 4},
    {"name": "Масло подсолнечное 1л", "price": 35000, "stock": 25, "category": 4},
    {"name": "Сахар 1кг", "price": 14000, "stock": 40, "category": 4},
    # Напитки
    {"name": "Вода 1.5л", "price": 6000, "stock": 60, "category": 5},
    {"name": "Чай чёрный 100г", "price": 18000, "stock": 20, "category": 5},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionFactory() as session:
        # Check if already seeded
        from sqlalchemy import select, func
        count = await session.scalar(select(func.count(Category.id)))
        if count > 0:
            print("✅ Database already seeded. Skipping.")
            return

        # Add categories
        cat_objects = []
        for cat_data in CATEGORIES:
            cat = Category(**cat_data)
            session.add(cat)
            cat_objects.append(cat)
        await session.flush()

        # Add products
        for prod_data in PRODUCTS:
            cat_idx = prod_data.pop("category")
            prod = Product(category_id=cat_objects[cat_idx].id, **prod_data)
            session.add(prod)

        await session.commit()
        print(f"✅ Seeded {len(CATEGORIES)} categories and {len(PRODUCTS)} products.")


if __name__ == "__main__":
    asyncio.run(seed())
