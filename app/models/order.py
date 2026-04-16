from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[str | None] = mapped_column(
        ForeignKey("customers.customer_id"), nullable=True
    )
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.employee_id"), nullable=True
    )
    order_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    required_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    shipped_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    freight: Mapped[float | None] = mapped_column(Float, nullable=True)
    ship_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ship_address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ship_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ship_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ship_postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ship_country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    customer = relationship("Customer", back_populates="orders")
    employee = relationship("Employee", back_populates="orders")
