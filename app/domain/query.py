from dataclasses import dataclass
from enum import Enum


class QueryIntent(str, Enum):
    COUNT_CUSTOMERS = "count_customers"
    COUNT_EMPLOYEES = "count_employees"
    COUNT_ORDERS = "count_orders"
    TOP_PRODUCTS_BY_STOCK = "top_products_by_stock"
    CUSTOMER_OVERVIEW = "customer_overview"


@dataclass(frozen=True)
class QueryPlan:
    intent: QueryIntent
    entity: str
    operation: str
    limit: int = 5

    def data_cache_key(self) -> str:
        return (
            f"data:{self.intent.value}:{self.entity}:" f"{self.operation}:{self.limit}"
        )
