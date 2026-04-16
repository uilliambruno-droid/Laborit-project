from collections.abc import Callable

from sqlalchemy import Select, func, inspect, select, text
from sqlalchemy.exc import SQLAlchemyError
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
                return {
                    "intent": intent_value,
                    "entity": query.entity,
                    "records": self._fetch_top_products_by_stock(session, query.limit),
                }

            return {
                "intent": intent_value,
                "entity": query.entity,
                "records": self._fetch_customer_overview(session, query.limit),
            }

    @staticmethod
    def _table_columns(session: Session, table_name: str) -> set[str]:
        bind = session.get_bind()
        if bind is None:
            return set()
        inspector = inspect(bind)
        return {column["name"] for column in inspector.get_columns(table_name)}

    @staticmethod
    def _pick_column(available: set[str], candidates: list[str]) -> str | None:
        for candidate in candidates:
            if candidate in available:
                return candidate
        return None

    def _fetch_customer_overview(
        self, session: Session, limit: int
    ) -> list[dict[str, object]]:
        columns = self._table_columns(session, "customers")
        customer_id_col = self._pick_column(
            columns, ["customer_id", "CustomerID", "id"]
        )
        company_col = self._pick_column(
            columns, ["company_name", "CompanyName", "company"]
        )
        contact_col = self._pick_column(columns, ["contact_name", "ContactName"])
        first_name_col = self._pick_column(columns, ["first_name", "FirstName"])
        last_name_col = self._pick_column(columns, ["last_name", "LastName"])
        country_col = self._pick_column(
            columns, ["country", "Country", "country_region"]
        )

        if customer_id_col is None:
            return []

        select_parts: list[str] = [f"`{customer_id_col}` AS customer_id"]
        select_parts.append(
            f"`{company_col}` AS company_name"
            if company_col
            else "NULL AS company_name"
        )

        if contact_col:
            select_parts.append(f"`{contact_col}` AS contact_name")
        elif first_name_col or last_name_col:
            first_expr = f"COALESCE(`{first_name_col}`, '')" if first_name_col else "''"
            last_expr = f"COALESCE(`{last_name_col}`, '')" if last_name_col else "''"
            select_parts.append(
                "TRIM(CONCAT("
                + first_expr
                + ", ' ', "
                + last_expr
                + ")) AS contact_name"
            )
        else:
            select_parts.append("NULL AS contact_name")

        select_parts.append(
            f"`{country_col}` AS country" if country_col else "NULL AS country"
        )

        order_col = company_col or customer_id_col
        statement = text(
            "SELECT "
            + ", ".join(select_parts)
            + " FROM customers"
            + f" ORDER BY `{order_col}` ASC"
            + " LIMIT :limit"
        )
        rows = session.execute(statement, {"limit": limit}).mappings().all()
        return [dict(row) for row in rows]

    def _fetch_top_products_by_stock(
        self,
        session: Session,
        limit: int,
    ) -> list[dict[str, object]]:
        columns = self._table_columns(session, "products")
        product_id_col = self._pick_column(columns, ["product_id", "ProductID", "id"])
        product_name_col = self._pick_column(columns, ["product_name", "ProductName"])
        stock_col = self._pick_column(
            columns,
            ["units_in_stock", "UnitsInStock", "target_level", "reorder_level"],
        )
        price_col = self._pick_column(
            columns,
            ["unit_price", "UnitPrice", "list_price", "standard_cost"],
        )

        if product_id_col is None or product_name_col is None:
            return []

        stock_expr = f"COALESCE(`{stock_col}`, 0)" if stock_col else "0"
        price_expr = f"COALESCE(`{price_col}`, 0)" if price_col else "0"

        statement = text(
            "SELECT "
            + f"`{product_id_col}` AS product_id, "
            + f"`{product_name_col}` AS product_name, "
            + f"{stock_expr} AS units_in_stock, "
            + f"{price_expr} AS unit_price "
            + "FROM products "
            + f"ORDER BY {stock_expr} DESC, `{product_name_col}` ASC "
            + "LIMIT :limit"
        )

        try:
            rows = session.execute(statement, {"limit": limit}).mappings().all()
            return [dict(row) for row in rows]
        except SQLAlchemyError:
            fallback_statement: Select[tuple[Product]] = (
                select(Product)
                .order_by(
                    func.coalesce(Product.units_in_stock, 0).desc(),
                    Product.product_name.asc(),
                )
                .limit(limit)
            )
            products = session.scalars(fallback_statement).all()
            return [
                {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "units_in_stock": product.units_in_stock or 0,
                    "unit_price": float(product.unit_price or 0),
                }
                for product in products
            ]
