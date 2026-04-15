from app.i18n import LLM_MESSAGES, detect_language


class LLMService:
    COUNT_INTENTS = {
        "count_customers",
        "count_employees",
        "count_orders",
    }

    def generate_text(self, user_input: str, data: dict[str, object]) -> str:
        intent = data.get("intent")
        language = detect_language(user_input)
        messages = LLM_MESSAGES[language]

        if intent == "count_customers":
            return messages["count_customers"].format(total=data["total"])

        if intent == "count_employees":
            return messages["count_employees"].format(total=data["total"])

        if intent == "count_orders":
            return messages["count_orders"].format(total=data["total"])

        if intent == "top_products_by_stock":
            records = data.get("records", [])
            if not records:
                return messages["no_products"]

            unit_label = messages["unit_label"]

            top_products = ", ".join(
                f"{record['product_name']} ({record['units_in_stock']} {unit_label})"
                for record in records
            )
            return messages["top_products"].format(top_products=top_products)

        records = data.get("records", [])
        if not records:
            return messages["no_customer_data"]

        companies = ", ".join(record["company_name"] for record in records[:5])
        return messages["customer_overview"].format(companies=companies)

    def generate_fallback_text(
        self, user_input: str, data: dict[str, object] | None = None
    ) -> str:
        language = detect_language(user_input)
        messages = LLM_MESSAGES[language]

        if data is None:
            return messages["fallback_no_data"]

        intent = data.get("intent")
        if intent in self.COUNT_INTENTS:
            total = data.get("total", 0)
            entity = str(data.get("entity", "records"))
            return messages["fallback_count"].format(total=total, entity=entity)

        records = data.get("records", [])
        if isinstance(records, list) and records:
            return messages["fallback_list"].format(records_count=len(records))

        return messages["fallback_generic"].format(user_input=user_input)

    def generate_guidance_text(self, user_input: str) -> str:
        language = detect_language(user_input)
        messages = LLM_MESSAGES[language]
        return messages["guidance"]
