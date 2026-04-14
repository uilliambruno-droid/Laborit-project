from collections.abc import Callable

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.domain.query import QueryIntent, QueryPlan
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.order import Order
from app.models.product import Product
from app.utils.database import get_session_factory


class DataService:
    def __init__(self, session_factory: Callable[[], Session] | None = None) -> None:
        self.session_factory = session_factory

    def fetch_data(self, query: QueryPlan) -> dict[str, object]:
        session_factory = self.session_factory or get_session_factory()
        intent_value = query.intent.value

        with session_factory() as session:
            if query.intent == QueryIntent.COUNT_CUSTOMERS:
                total = session.scalar(select(func.count()).select_from(Customer)) or 0
                return {
                    "intent": intent_value,
                    "entity": query.entity,
                    "total": int(total),
                }

            if query.intent == QueryIntent.COUNT_EMPLOYEES:
                total = session.scalar(select(func.count()).select_from(Employee)) or 0
                return {
                    "intent": intent_value,
                    "entity": query.entity,
                    "total": int(total),
                }

            if query.intent == QueryIntent.COUNT_ORDERS:
                total = session.scalar(select(func.count()).select_from(Order)) or 0
                return {
                    "intent": intent_value,
                    "entity": query.entity,
                    "total": int(total),
                }

            if query.intent == QueryIntent.TOP_PRODUCTS_BY_STOCK:
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
                    "intent": intent_value,
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
                "intent": intent_value,
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
