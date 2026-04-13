from dataclasses import dataclass

from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class QueryPlan:
    intent: str
    entity: str
    operation: str
    limit: int = 5


class QueryService:
    def _log_plan(self, plan: QueryPlan) -> QueryPlan:
        logger.debug(
            "query_service_plan_resolved",
            intent=plan.intent,
            entity=plan.entity,
            operation=plan.operation,
        )
        return plan

    def build_query(self, user_input: str) -> QueryPlan:
        normalized = user_input.strip().lower()
        logger.debug("query_service_input", input_length=len(user_input))

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
                return self._log_plan(
                    QueryPlan(
                        intent="count_customers",
                        entity="customers",
                        operation="count",
                    )
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
                return self._log_plan(
                    QueryPlan(
                        intent="count_employees",
                        entity="employees",
                        operation="count",
                    )
                )
            if any(
                word in normalized for word in ["order", "orders", "pedido", "pedidos"]
            ):
                return self._log_plan(
                    QueryPlan(intent="count_orders", entity="orders", operation="count")
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
            return self._log_plan(
                QueryPlan(
                    intent="top_products_by_stock",
                    entity="products",
                    operation="list",
                    limit=5,
                )
            )

        plan = QueryPlan(
            intent="customer_overview", entity="customers", operation="list", limit=5
        )
        return self._log_plan(plan)
