from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.decorators import admin_only
from bot.utils.formatters import fmt_uzs
from bot.keyboards.admin_kb import cancel_keyboard, admin_main_keyboard, categories_inline, product_actions_keyboard
from db.repositories.product_repo import get_categories, get_products_by_category, get_product
from db.models.product import Product
from db.models.category import Category

router = Router()


class AddProductFSM(StatesGroup):
    category = State()
    name = State()
    price = State()
    stock = State()
    photo = State()
    description = State()


class EditProductFSM(StatesGroup):
    waiting_price = State()
    waiting_stock = State()


# ─── MAIN PRODUCT MENU ────────────────────────────────────────────────────

@router.message(F.text == "📦 Управление товарами")
@admin_only
async def cmd_products(message: Message, session: AsyncSession, **kwargs):
    cats = await get_categories(session)
    if not cats:
        await message.answer(
            "📦 Нет категорий. Сначала добавьте категорию.",
            reply_markup=categories_inline([]),
        )
        return
    await message.answer(
        "📦 <b>Управление товарами</b>\n\nВыберите категорию:",
        reply_markup=categories_inline(cats),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_cat:"))
@admin_only
async def admin_select_category(call: CallbackQuery, session: AsyncSession, **kwargs):
    cat_id = call.data.split(":")[1]
    if cat_id == "new":
        await call.message.answer("Введите название новой категории:")
        await call.answer()
        return

    products = await get_products_by_category(session, int(cat_id))
    if not products:
        await call.message.edit_text(
            "В этой категории нет товаров.\n\nДобавить новый товар /add_product"
        )
        await call.answer()
        return

    text = "📦 <b>Товары:</b>\n\n"
    for p in products:
        stock_emoji = "✅" if p.stock > 0 else "❌"
        text += f"{stock_emoji} <b>{p.name}</b> — {fmt_uzs(p.price)} | Остаток: {p.stock}\n"
    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()


# ─── ADD PRODUCT ──────────────────────────────────────────────────────────

@router.message(F.text == "/add_product")
@admin_only
async def cmd_add_product(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    cats = await get_categories(session)
    if not cats:
        await message.answer("Сначала добавьте категорию.")
        return

    text = "Выберите категорию (введите номер):\n\n"
    for i, cat in enumerate(cats, 1):
        text += f"{i}. {cat.icon or '📁'} {cat.name}\n"

    await state.update_data(categories={str(i): cat.id for i, cat in enumerate(cats, 1)})
    await message.answer(text, reply_markup=cancel_keyboard())
    await state.set_state(AddProductFSM.category)


@router.message(StateFilter(AddProductFSM.category))
@admin_only
async def add_product_category(message: Message, state: FSMContext, **kwargs):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=admin_main_keyboard())
        return
    data = await state.get_data()
    cat_id = data["categories"].get(message.text.strip())
    if not cat_id:
        await message.answer("❌ Введите корректный номер.")
        return
    await state.update_data(category_id=cat_id)
    await message.answer("Введите <b>название товара</b>:", parse_mode="HTML")
    await state.set_state(AddProductFSM.name)


@router.message(StateFilter(AddProductFSM.name))
@admin_only
async def add_product_name(message: Message, state: FSMContext, **kwargs):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=admin_main_keyboard())
        return
    await state.update_data(name=message.text.strip())
    await message.answer("Введите <b>цену</b> (в UZS):", parse_mode="HTML")
    await state.set_state(AddProductFSM.price)


@router.message(StateFilter(AddProductFSM.price))
@admin_only
async def add_product_price(message: Message, state: FSMContext, **kwargs):
    try:
        price = float(message.text.replace(" ", "").replace(",", "."))
        if price <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Введите корректную цену.")
        return
    await state.update_data(price=price)
    await message.answer("Введите <b>остаток</b> (количество):", parse_mode="HTML")
    await state.set_state(AddProductFSM.stock)


@router.message(StateFilter(AddProductFSM.stock))
@admin_only
async def add_product_stock(message: Message, state: FSMContext, **kwargs):
    try:
        stock = int(message.text.strip())
        if stock < 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Введите целое неотрицательное число.")
        return
    await state.update_data(stock=stock)
    await message.answer(
        "Отправьте <b>фото товара</b> или /skip для пропуска:",
        parse_mode="HTML",
    )
    await state.set_state(AddProductFSM.photo)


@router.message(StateFilter(AddProductFSM.photo))
@admin_only
async def add_product_photo(message: Message, state: FSMContext, **kwargs):
    photo_file_id = None
    if message.text == "/skip":
        pass
    elif message.photo:
        photo_file_id = message.photo[-1].file_id
    else:
        await message.answer("Отправьте фото или /skip")
        return

    await state.update_data(photo_file_id=photo_file_id)
    await message.answer(
        "Введите <b>описание</b> или /skip:",
        parse_mode="HTML",
    )
    await state.set_state(AddProductFSM.description)


@router.message(StateFilter(AddProductFSM.description))
@admin_only
async def add_product_description(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    description = None if message.text == "/skip" else message.text.strip()
    data = await state.get_data()

    product = Product(
        name=data["name"],
        price=data["price"],
        stock=data["stock"],
        category_id=data["category_id"],
        photo_file_id=data.get("photo_file_id"),
        description=description,
    )
    session.add(product)
    await session.flush()

    await message.answer(
        f"✅ <b>Товар добавлен!</b>\n\n"
        f"📦 {product.name}\n"
        f"💰 {fmt_uzs(product.price)}\n"
        f"🏷 Остаток: {product.stock}",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML",
    )
    await state.clear()


# ─── EDIT PRODUCT ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("prod_price:"))
@admin_only
async def edit_product_price_start(call: CallbackQuery, state: FSMContext, **kwargs):
    product_id = int(call.data.split(":")[1])
    await state.update_data(product_id=product_id)
    await call.message.answer("Введите новую цену (UZS):", reply_markup=cancel_keyboard())
    await state.set_state(EditProductFSM.waiting_price)
    await call.answer()


@router.message(StateFilter(EditProductFSM.waiting_price))
@admin_only
async def edit_product_price_save(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    try:
        price = float(message.text.replace(" ", "").replace(",", "."))
    except ValueError:
        await message.answer("❌ Некорректная цена.")
        return
    data = await state.get_data()
    product = await get_product(session, data["product_id"])
    if product:
        product.price = price
        await message.answer(
            f"✅ Цена товара <b>{product.name}</b> обновлена: {fmt_uzs(price)}",
            reply_markup=admin_main_keyboard(),
            parse_mode="HTML",
        )
    await state.clear()


@router.callback_query(F.data.startswith("prod_stock:"))
@admin_only
async def edit_product_stock_start(call: CallbackQuery, state: FSMContext, **kwargs):
    product_id = int(call.data.split(":")[1])
    await state.update_data(product_id=product_id)
    await call.message.answer("Введите новый остаток:", reply_markup=cancel_keyboard())
    await state.set_state(EditProductFSM.waiting_stock)
    await call.answer()


@router.message(StateFilter(EditProductFSM.waiting_stock))
@admin_only
async def edit_product_stock_save(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    try:
        stock = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректное значение.")
        return
    data = await state.get_data()
    product = await get_product(session, data["product_id"])
    if product:
        product.stock = stock
        product.is_available = stock > 0
        await message.answer(
            f"✅ Остаток <b>{product.name}</b> обновлён: {stock}",
            reply_markup=admin_main_keyboard(),
            parse_mode="HTML",
        )
    await state.clear()


@router.callback_query(F.data.startswith("prod_toggle:"))
@admin_only
async def toggle_product(call: CallbackQuery, session: AsyncSession, **kwargs):
    product_id = int(call.data.split(":")[1])
    product = await get_product(session, product_id)
    if product:
        product.is_available = not product.is_available
        status = "показан" if product.is_available else "скрыт"
        await call.message.edit_text(
            f"✅ Товар <b>{product.name}</b> {status}.",
            parse_mode="HTML",
        )
    await call.answer()
