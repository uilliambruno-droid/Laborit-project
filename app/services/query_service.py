from dataclasses import dataclass


@dataclass(frozen=True)
class QueryPlan:
    intent: str
    entity: str
    operation: str
    limit: int = 5


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
                    intent="count_customers", entity="customers", operation="count"
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
                    intent="count_employees", entity="employees", operation="count"
                )
            if any(
                word in normalized for word in ["order", "orders", "pedido", "pedidos"]
            ):
                return QueryPlan(
                    intent="count_orders", entity="orders", operation="count"
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
                intent="top_products_by_stock",
                entity="products",
                operation="list",
                limit=5,
            )

        return QueryPlan(
            intent="customer_overview", entity="customers", operation="list", limit=5
        )
