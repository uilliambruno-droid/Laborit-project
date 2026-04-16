LLM_MESSAGES_EN = {
    "count_customers": "There are {total} customers available in the current portfolio dataset.",
    "count_employees": "There are {total} employees available in the current portfolio dataset.",
    "count_orders": "There are {total} orders registered in the current portfolio dataset.",
    "no_products": "No products were found for the current stock overview.",
    "top_products": "Top products by stock are: {top_products}.",
    "no_customer_data": "No customer data was found to answer this question.",
    "customer_overview": (
        "Based on the available customer overview, consider starting with these accounts: "
        "{companies}."
    ),
    "fallback_no_data": (
        "We could not complete the enriched analysis right now, but the request was "
        "received and can be retried shortly."
    ),
    "fallback_count": "Current fallback summary: there are {total} {entity} available.",
    "fallback_list": "Current fallback summary: {records_count} records were retrieved for the request.",
    "fallback_generic": (
        "We received the question '{user_input}', but a richer generated answer is "
        "temporarily unavailable."
    ),
    "guidance": (
        "I can help with commercial analytics from the Northwind portfolio. "
        "Try one of these:\n"
        "- How many customers do we have?\n"
        "- How many employees are registered?\n"
        "- What is the total number of orders?\n"
        "- Show me the top products by stock\n"
        "- Give me an overview of our customers"
    ),
    "unit_label": "units",
}

VALIDATION_MESSAGES_BY_TYPE_EN = {
    "string_too_short": "Question must have at least 5 characters.",
    "string_too_long": "Question must have at most 500 characters.",
    "extra_forbidden": "Unexpected field was sent in the request body.",
}

VALIDATION_MESSAGES_BY_CONTENT_EN = {
    "cannot be blank": "Question cannot be blank.",
    "too many consecutive question marks": "Question has too many question marks.",
}

VALIDATION_DEFAULT_MESSAGE_EN = "Invalid request value."
VALIDATION_PAYLOAD_MESSAGE_EN = (
    "Invalid request payload. Check the fields and try again."
)
