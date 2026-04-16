from app.i18n.messages_en import (
    LLM_MESSAGES_EN,
    VALIDATION_DEFAULT_MESSAGE_EN,
    VALIDATION_MESSAGES_BY_CONTENT_EN,
    VALIDATION_MESSAGES_BY_TYPE_EN,
    VALIDATION_PAYLOAD_MESSAGE_EN,
)
from app.i18n.messages_pt import (
    LLM_MESSAGES_PT,
    VALIDATION_DEFAULT_MESSAGE_PT,
    VALIDATION_MESSAGES_BY_CONTENT_PT,
    VALIDATION_MESSAGES_BY_TYPE_PT,
    VALIDATION_PAYLOAD_MESSAGE_PT,
)

LANG_EN = "en"
LANG_PT = "pt"

PT_LANGUAGE_HINTS = (
    "olá",
    "ola",
    "oi",
    "tudo bem",
    "contigo",
    "bom dia",
    "boa tarde",
    "boa noite",
    "quantos",
    "qtd",
    "clientes",
    "cliente",
    "pedidos",
    "pedido",
    "estoque",
    "produto",
    "produtos",
    "visão",
    "visao",
    "resumo",
)

BASIC_QUESTION_HINTS = {
    LANG_EN: (
        "hello",
        "hi",
        "hey",
        "how are you",
        "tell me something",
        "good morning",
        "good afternoon",
        "good evening",
    ),
    LANG_PT: (
        "olá",
        "ola",
        "oi",
        "tudo bem",
        "contigo",
        "me fale algo",
        "fala algo",
        "bom dia",
        "boa tarde",
        "boa noite",
    ),
}

QUERY_KEYWORDS = {
    "count_tokens": ["how many", "count", "total", "quantos", "qtd"],
    "customer_tokens": [
        "customer",
        "customers",
        "client",
        "clients",
        "cliente",
        "clientes",
    ],
    "employee_tokens": [
        "employee",
        "employees",
        "manager",
        "managers",
        "gerente",
        "gerentes",
    ],
    "order_tokens": ["order", "orders", "pedido", "pedidos"],
    "product_tokens": [
        "product",
        "products",
        "produto",
        "produtos",
        "stock",
        "inventory",
        "estoque",
    ],
}

LLM_MESSAGES = {LANG_EN: LLM_MESSAGES_EN, LANG_PT: LLM_MESSAGES_PT}

VALIDATION_MESSAGES_BY_TYPE = {
    "string_too_short": {
        LANG_EN: VALIDATION_MESSAGES_BY_TYPE_EN["string_too_short"],
        LANG_PT: VALIDATION_MESSAGES_BY_TYPE_PT["string_too_short"],
    },
    "string_too_long": {
        LANG_EN: VALIDATION_MESSAGES_BY_TYPE_EN["string_too_long"],
        LANG_PT: VALIDATION_MESSAGES_BY_TYPE_PT["string_too_long"],
    },
    "extra_forbidden": {
        LANG_EN: VALIDATION_MESSAGES_BY_TYPE_EN["extra_forbidden"],
        LANG_PT: VALIDATION_MESSAGES_BY_TYPE_PT["extra_forbidden"],
    },
}

VALIDATION_MESSAGES_BY_CONTENT = {
    "cannot be blank": {
        LANG_EN: VALIDATION_MESSAGES_BY_CONTENT_EN["cannot be blank"],
        LANG_PT: VALIDATION_MESSAGES_BY_CONTENT_PT["cannot be blank"],
    },
    "too many consecutive question marks": {
        LANG_EN: VALIDATION_MESSAGES_BY_CONTENT_EN[
            "too many consecutive question marks"
        ],
        LANG_PT: VALIDATION_MESSAGES_BY_CONTENT_PT[
            "too many consecutive question marks"
        ],
    },
}

VALIDATION_DEFAULT_MESSAGE = {
    LANG_EN: VALIDATION_DEFAULT_MESSAGE_EN,
    LANG_PT: VALIDATION_DEFAULT_MESSAGE_PT,
}

VALIDATION_PAYLOAD_MESSAGE = {
    LANG_EN: VALIDATION_PAYLOAD_MESSAGE_EN,
    LANG_PT: VALIDATION_PAYLOAD_MESSAGE_PT,
}


def detect_language(user_input: str) -> str:
    normalized = user_input.strip().lower()
    if any(hint in normalized for hint in PT_LANGUAGE_HINTS):
        return LANG_PT
    if any(char in normalized for char in "ãáàâçéêíóôõú"):
        return LANG_PT
    return LANG_EN


def is_basic_question(user_input: str) -> bool:
    normalized = user_input.strip().lower()
    all_analytics_keywords = {
        token for tokens in QUERY_KEYWORDS.values() for token in tokens
    }
    if any(keyword in normalized for keyword in all_analytics_keywords):
        return False

    return any(
        hint in normalized for hints in BASIC_QUESTION_HINTS.values() for hint in hints
    )


def get_validation_messages(error_type: str, raw_message: str) -> tuple[str, str]:
    if error_type in VALIDATION_MESSAGES_BY_TYPE:
        mapping = VALIDATION_MESSAGES_BY_TYPE[error_type]
        return mapping[LANG_EN], mapping[LANG_PT]

    normalized = raw_message.lower()
    for signal, mapping in VALIDATION_MESSAGES_BY_CONTENT.items():
        if signal in normalized:
            return mapping[LANG_EN], mapping[LANG_PT]

    return VALIDATION_DEFAULT_MESSAGE[LANG_EN], VALIDATION_DEFAULT_MESSAGE[LANG_PT]
