from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.routers import (
    auth,
    categories,
    suppliers,
    products,
    imports,
    exports,
    inventory,
    proposals,
    reports
)

# Import all models to register them with SQLAlchemy Base
import app.models.user
import app.models.category
import app.models.supplier
import app.models.product
import app.models.import_order
import app.models.export_order
import app.models.proposal

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hệ thống Quản lý Tồn kho Căng tin CTECH",
    description="Hệ thống MVP Quản lý Tồn kho & Đề xuất Nhập hàng - Báo cáo Cao học CTECH",
    version="1.0.0"
)

# CORS configuration: Hỗ trợ localhost, Vercel, Render và mọi origin qua regex
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["suppliers"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(imports.router, prefix="/api/imports", tags=["imports"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(proposals.router, prefix="/api/proposals", tags=["proposals"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

@app.get("/")
def root():
    return {
        "system": "CTECH Canteen Inventory Management System",
        "status": "online",
        "docs_url": "/docs"
    }
