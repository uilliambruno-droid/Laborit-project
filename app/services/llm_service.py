from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    def generate_text(self, user_input: str, data: dict[str, object]) -> str:
        intent = data.get("intent")
        logger.debug("llm_service_generate_start", intent=intent)

        if intent == "count_customers":
            text = f"There are {data['total']} customers available in the current portfolio dataset."
            logger.debug(
                "llm_service_generate_done", intent=intent, answer_length=len(text)
            )
            return text

        if intent == "count_employees":
            text = f"There are {data['total']} employees available in the current portfolio dataset."
            logger.debug(
                "llm_service_generate_done", intent=intent, answer_length=len(text)
            )
            return text

        if intent == "count_orders":
            text = f"There are {data['total']} orders registered in the current portfolio dataset."
            logger.debug(
                "llm_service_generate_done", intent=intent, answer_length=len(text)
            )
            return text

        if intent == "top_products_by_stock":
            records = data.get("records", [])
            if not records:
                text = "No products were found for the current stock overview."
                logger.debug(
                    "llm_service_generate_done", intent=intent, answer_length=len(text)
                )
                return text

            top_products = ", ".join(
                f"{record['product_name']} ({record['units_in_stock']} units)"
                for record in records
            )
            text = f"Top products by stock are: {top_products}."
            logger.debug(
                "llm_service_generate_done", intent=intent, answer_length=len(text)
            )
            return text

        records = data.get("records", [])
        if not records:
            text = "No customer data was found to answer this question."
            logger.debug(
                "llm_service_generate_done", intent=intent, answer_length=len(text)
            )
            return text

        companies = ", ".join(record["company_name"] for record in records[:5])
        text = (
            "Based on the available customer overview, consider starting with these accounts: "
            f"{companies}."
        )
        logger.debug(
            "llm_service_generate_done", intent=intent, answer_length=len(text)
        )
        return text

    def generate_fallback_text(
        self, user_input: str, data: dict[str, object] | None = None
    ) -> str:
        logger.warning("llm_service_fallback_start", has_data=data is not None)
        if data is None:
            text = (
                "We could not complete the enriched analysis right now, "
                "but the request was received and can be retried shortly."
            )
            logger.warning("llm_service_fallback_done", answer_length=len(text))
            return text

        intent = data.get("intent")
        if intent in {"count_customers", "count_employees", "count_orders"}:
            total = data.get("total", 0)
            entity = str(data.get("entity", "records"))
            text = f"Current fallback summary: there are {total} {entity} available."
            logger.warning(
                "llm_service_fallback_done", intent=intent, answer_length=len(text)
            )
            return text

        records = data.get("records", [])
        if isinstance(records, list) and records:
            text = f"Current fallback summary: {len(records)} records were retrieved for the request."
            logger.warning(
                "llm_service_fallback_done", intent=intent, answer_length=len(text)
            )
            return text

        text = (
            f"We received the question '{user_input}', but a richer generated answer "
            "is temporarily unavailable."
        )
        logger.warning(
            "llm_service_fallback_done", intent=intent, answer_length=len(text)
        )
        return text
