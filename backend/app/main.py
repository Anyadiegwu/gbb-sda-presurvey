from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import FRONTEND_URL
from app.core.database import init_db

from app.features.auth.router import router as auth_router
from app.features.manholes.router import router as manholes_admin_router
from app.features.boq_items.router import router as boq_items_admin_router
from app.features.formula.router import router as formula_admin_router
from app.features.routes.router import router as routes_admin_router
from app.features.quotes.router import router as quotes_router
from app.features.submissions.router import public_router as submissions_public_router, admin_router as submissions_admin_router

app = FastAPI(title="Fiber BOQ API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Quick-start table creation for development. Swap for Alembic
    # migrations before running this against a real production database.
    init_db()


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Admin-only routers (protected inside each router via get_current_admin)
app.include_router(auth_router)
app.include_router(manholes_admin_router)
app.include_router(boq_items_admin_router)
app.include_router(formula_admin_router)
app.include_router(routes_admin_router)
app.include_router(submissions_admin_router)

# Public/customer-facing routers
app.include_router(quotes_router)
app.include_router(submissions_public_router)
