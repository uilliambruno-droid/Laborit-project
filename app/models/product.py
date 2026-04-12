from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_name: Mapped[str] = mapped_column(String(100))
    supplier_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity_per_unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    units_in_stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    units_on_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reorder_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discontinued: Mapped[bool] = mapped_column(Boolean, default=False)
