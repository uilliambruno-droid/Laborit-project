from collections.abc import Callable

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.employee import Employee
from app.models.order import Order
from app.models.product import Product
from app.services.query_service import QueryPlan
from app.utils.database import get_session_factory


class DataService:
    def __init__(self, session_factory: Callable[[], Session] | None = None) -> None:
        self.session_factory = session_factory

    def fetch_data(self, query: QueryPlan) -> dict[str, object]:
        session_factory = self.session_factory or get_session_factory()

        with session_factory() as session:
            if query.intent == "count_customers":
                total = session.scalar(select(func.count()).select_from(Customer)) or 0
                return {
                    "intent": query.intent,
                    "entity": query.entity,
                    "total": int(total),
                }

            if query.intent == "count_employees":
                total = session.scalar(select(func.count()).select_from(Employee)) or 0
                return {
                    "intent": query.intent,
                    "entity": query.entity,
                    "total": int(total),
                }

            if query.intent == "count_orders":
                total = session.scalar(select(func.count()).select_from(Order)) or 0
                return {
                    "intent": query.intent,
                    "entity": query.entity,
                    "total": int(total),
                }

            if query.intent == "top_products_by_stock":
                statement: Select[tuple[Product]] = (
                    select(Product)
                    .order_by(
                        func.coalesce(Product.units_in_stock, 0).desc(),
                        Product.product_name.asc(),
                    )
                    .limit(query.limit)
                )
                products = session.scalars(statement).all()
                return {
                    "intent": query.intent,
                    "entity": query.entity,
                    "records": [
                        {
                            "product_id": product.product_id,
                            "product_name": product.product_name,
                            "units_in_stock": product.units_in_stock or 0,
                            "unit_price": float(product.unit_price or 0),
                        }
                        for product in products
                    ],
                }

            statement = (
                select(Customer)
                .order_by(Customer.company_name.asc())
                .limit(query.limit)
            )
            customers = session.scalars(statement).all()
            return {
                "intent": query.intent,
                "entity": query.entity,
                "records": [
                    {
                        "customer_id": customer.customer_id,
                        "company_name": customer.company_name,
                        "contact_name": customer.contact_name,
                        "country": customer.country,
                    }
                    for customer in customers
                ],
            }
