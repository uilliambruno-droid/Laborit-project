from app.domain.query import QueryIntent, QueryPlan


class QueryService:
    def build_query(self, user_input: str) -> QueryPlan:
        normalized = user_input.strip().lower()

        if any(
            word in normalized
            for word in ["how many", "count", "total", "quantos", "qtd"]
        ):
            if any(
                word in normalized
                for word in [
                    "customer",
                    "customers",
                    "client",
                    "clients",
                    "cliente",
                    "clientes",
                ]
            ):
                return QueryPlan(
                    intent=QueryIntent.COUNT_CUSTOMERS,
                    entity="customers",
                    operation="count",
                )
            if any(
                word in normalized
                for word in [
                    "employee",
                    "employees",
                    "manager",
                    "managers",
                    "gerente",
                    "gerentes",
                ]
            ):
                return QueryPlan(
                    intent=QueryIntent.COUNT_EMPLOYEES,
                    entity="employees",
                    operation="count",
                )
            if any(
                word in normalized for word in ["order", "orders", "pedido", "pedidos"]
            ):
                return QueryPlan(
                    intent=QueryIntent.COUNT_ORDERS,
                    entity="orders",
                    operation="count",
                )

        if any(
            word in normalized
            for word in [
                "product",
                "products",
                "produto",
                "produtos",
                "stock",
                "inventory",
                "estoque",
            ]
        ):
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
