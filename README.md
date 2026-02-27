# 🛒 Telegram ERP Bot — Продуктовый магазин (Бухара, Узбекистан)

Полнофункциональная ERP-система на базе Telegram-бота для малого продуктового магазина. Заменяет бумажную тетрадь учёта долгов (nasiya) и предоставляет онлайн-витрину через Telegram Web App.

---

## 🚀 Быстрый старт

### 1. Клонировать и настроить окружение

```bash
cp .env.example .env
# Откройте .env и заполните значения:
#   BOT_TOKEN — токен от @BotFather
#   ADMIN_IDS — ваш Telegram ID (узнать у @userinfobot)
#   WEBAPP_URL — URL задеплоенного React-приложения
```

### 2. Запуск через Docker (рекомендуется)

```bash
docker-compose up -d --build
```

### 3. Запуск вручную (для разработки)

```bash
# Установить зависимости
pip install -r requirements.txt

# Создать таблицы и заполнить тестовыми данными
python seed.py

# Запустить бот
python -m bot.main

# В отдельном терминале — API для Web App
uvicorn api.main:app --reload --port 8000

# Web App (в папке webapp/)
cd webapp && npm install && npm start
```

---

## 📁 Структура проекта

```
erp_bot/
├── bot/                    # Aiogram 3.x бот
│   ├── main.py             # Точка входа
│   ├── config.py           # Настройки (pydantic-settings)
│   ├── handlers/
│   │   ├── admin/          # Handlers для администратора
│   │   │   ├── nasiya.py   # Запись/погашение долга (FSM)
│   │   │   ├── products.py # CRUD товаров (FSM)
│   │   │   ├── analytics.py# Отчёты и поиск клиентов
│   │   │   └── broadcast.py# Рассылки по сегментам
│   │   └── client/         # Handlers для покупателей
│   │       ├── profile.py  # /start, регистрация, контакт
│   │       ├── balance.py  # Просмотр долга и истории
│   │       └── orders.py   # История заказов
│   ├── keyboards/          # Клавиатуры Telegram
│   ├── services/           # Бизнес-логика
│   │   ├── nasiya_service.py    # Атомарные операции с долгом
│   │   ├── notification.py      # Отправка уведомлений
│   │   └── analytics_service.py # Дневная аналитика
│   ├── middlewares/        # DbSession + Auth middlewares
│   └── utils/              # Форматтеры, декораторы
├── db/                     # SQLAlchemy
│   ├── base.py             # Engine, Session, Base
│   ├── models/             # ORM модели
│   └── repositories/       # Запросы к БД
├── api/                    # FastAPI (для Web App)
│   ├── main.py
│   ├── deps.py             # Верификация Telegram initData
│   └── routers/            # /catalog, /orders
├── webapp/                 # React Telegram Web App
│   └── src/
│       ├── App.jsx         # Главный компонент
│       ├── pages/          # Catalog, Cart, Checkout
│       ├── hooks/          # useTelegramUser
│       └── api/            # Axios клиент
├── alembic/                # Миграции БД
├── seed.py                 # Начальные данные
└── docker-compose.yml
```

---

## 👥 Роли и команды

### Администратор
| Кнопка / Команда | Функция |
|---|---|
| 📝 Записать долг | FSM-диалог: поиск клиента → сумма → подтверждение |
| 💳 Погасить долг | FSM-диалог: поиск → сумма → подтверждение |
| 📊 Аналитика | Дневной отчёт: выручка, долги, топ-должники |
| 📦 Управление товарами | Просмотр/добавление/редактирование товаров |
| 📣 Рассылка | Сегментированные сообщения клиентам |
| /client `<ID>` | Полный профиль клиента + история транзакций |

### Клиент
| Кнопка | Функция |
|---|---|
| 🛒 Магазин | Открывает Telegram Web App с каталогом |
| 💰 Мой баланс | Текущий долг + история nasiya |
| 📜 История покупок | Список заказов |
| 📞 Мой профиль | Личные данные |

---

## 🏗 Схема базы данных

```
users           — клиенты и администраторы (nasiya_balance)
categories      — категории товаров
products        — товары (цена, остаток, фото)
orders          — заказы (cash/nasiya/card, pickup/delivery)
order_items     — позиции заказа
transactions    — НЕИЗМЕНЯЕМЫЙ LEDGER всех изменений долга
                  (balance_before, balance_after, admin_id)
```

---

## 🔐 Безопасность

- **Разграничение ролей**: `is_admin` в БД + `@admin_only` декоратор
- **Race conditions**: `SELECT FOR UPDATE` при изменении баланса
- **Web App**: HMAC-SHA256 верификация `initData` от Telegram
- **Параметризованные запросы**: SQLAlchemy ORM защищает от SQL-инъекций

---

## ⚙️ Переменные окружения (.env)

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `ADMIN_IDS` | Telegram ID администраторов через запятую |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | `redis://localhost:6379/0` (для FSM хранилища) |
| `WEBAPP_URL` | URL задеплоенного React Web App |

---

## 📦 Деплой на VPS (Ubuntu)

```bash
# 1. Установить Docker
curl -fsSL https://get.docker.com | sh

# 2. Клонировать проект, заполнить .env
git clone <repo> && cd erp_bot
cp .env.example .env && nano .env

# 3. Запустить
docker-compose up -d --build

# 4. Засеять начальные данные
docker-compose exec bot python seed.py

# 5. Настроить Nginx + SSL для Web App (certbot)
# WEBAPP_URL должен быть HTTPS для Telegram Web App!
```

---

## 📲 Настройка Web App в BotFather

1. Написать @BotFather → `/newapp`
2. Указать URL задеплоенного webapp
3. Скопировать ссылку на WebApp
4. Вставить в `WEBAPP_URL` в `.env`

---

## 🧪 Тестирование

```bash
# Запустить бота локально с тестовым .env
BOT_TOKEN=xxx ADMIN_IDS=<ваш_id> DATABASE_URL=... python -m bot.main
```

Узнать свой Telegram ID: написать боту @userinfobot
