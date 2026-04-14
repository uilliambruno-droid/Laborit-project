class LLMService:
    COUNT_INTENTS = {
        "count_customers",
        "count_employees",
        "count_orders",
    }

    def generate_text(self, user_input: str, data: dict[str, object]) -> str:
        intent = data.get("intent")

        if intent == "count_customers":
            return f"There are {data['total']} customers available in the current portfolio dataset."

        if intent == "count_employees":
            return f"There are {data['total']} employees available in the current portfolio dataset."

        if intent == "count_orders":
            return f"There are {data['total']} orders registered in the current portfolio dataset."

        if intent == "top_products_by_stock":
            records = data.get("records", [])
            if not records:
                return "No products were found for the current stock overview."

            top_products = ", ".join(
                f"{record['product_name']} ({record['units_in_stock']} units)"
                for record in records
            )
            return f"Top products by stock are: {top_products}."

        records = data.get("records", [])
        if not records:
            return "No customer data was found to answer this question."

        companies = ", ".join(record["company_name"] for record in records[:5])
        return (
            "Based on the available customer overview, consider starting with these accounts: "
            f"{companies}."
        )

    def generate_fallback_text(
        self, user_input: str, data: dict[str, object] | None = None
    ) -> str:
        if data is None:
            return (
                "We could not complete the enriched analysis right now, "
                "but the request was received and can be retried shortly."
            )

        intent = data.get("intent")
        if intent in self.COUNT_INTENTS:
            total = data.get("total", 0)
            entity = str(data.get("entity", "records"))
            return f"Current fallback summary: there are {total} {entity} available."

        records = data.get("records", [])
        if isinstance(records, list) and records:
            return f"Current fallback summary: {len(records)} records were retrieved for the request."

        return (
            f"We received the question '{user_input}', but a richer generated answer "
            "is temporarily unavailable."
        )
