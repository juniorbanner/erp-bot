from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import catalog, orders

app = FastAPI(
    title="ERP Bot API",
    description="API for Telegram Web App — продуктовый магазин Бухара",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: restrict to your webapp domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(orders.router)


# @app.get("/health")
# async def health():
#     return {"status": "ok"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "ok"}
