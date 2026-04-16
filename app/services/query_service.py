from app.domain.query import QueryIntent, QueryPlan
from app.i18n import QUERY_KEYWORDS


class QueryService:
    def build_query(self, user_input: str) -> QueryPlan:
        normalized = user_input.strip().lower()

        if any(word in normalized for word in QUERY_KEYWORDS["count_tokens"]):
            if any(word in normalized for word in QUERY_KEYWORDS["customer_tokens"]):
                return QueryPlan(
                    intent=QueryIntent.COUNT_CUSTOMERS,
                    entity="customers",
                    operation="count",
                )
            if any(word in normalized for word in QUERY_KEYWORDS["employee_tokens"]):
                return QueryPlan(
                    intent=QueryIntent.COUNT_EMPLOYEES,
                    entity="employees",
                    operation="count",
                )
            if any(word in normalized for word in QUERY_KEYWORDS["order_tokens"]):
                return QueryPlan(
                    intent=QueryIntent.COUNT_ORDERS,
                    entity="orders",
                    operation="count",
                )

        if any(word in normalized for word in QUERY_KEYWORDS["product_tokens"]):
            return QueryPlan(
                intent=QueryIntent.TOP_PRODUCTS_BY_STOCK,
                entity="products",
                operation="list",
                limit=5,
            )

        return QueryPlan(
            intent=QueryIntent.CUSTOMER_OVERVIEW,
            entity="customers",
            operation="list",
            limit=5,
        )
