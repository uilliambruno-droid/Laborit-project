LLM_MESSAGES_PT = {
    "count_customers": "Existem {total} clientes disponíveis no portfólio atual.",
    "count_employees": "Existem {total} colaboradores disponíveis no portfólio atual.",
    "count_orders": "Existem {total} pedidos registrados no portfólio atual.",
    "no_products": "Nenhum produto foi encontrado para a visão atual de estoque.",
    "top_products": "Os principais produtos por estoque são: {top_products}.",
    "no_customer_data": "Nenhum dado de clientes foi encontrado para responder esta pergunta.",
    "customer_overview": (
        "Com base na visão geral de clientes disponível, considere começar por estas "
        "contas: {companies}."
    ),
    "fallback_no_data": (
        "Não conseguimos concluir a análise enriquecida agora, mas a solicitação foi "
        "recebida e pode ser tentada novamente em instantes."
    ),
    "fallback_count": "Resumo de contingência: existem {total} {entity} disponíveis.",
    "fallback_list": "Resumo de contingência: {records_count} registros foram recuperados para a solicitação.",
    "fallback_generic": (
        "Recebemos a pergunta '{user_input}', mas uma resposta gerada mais rica está "
        "temporariamente indisponível."
    ),
    "guidance": (
        "Posso ajudar com análises comerciais do portfólio Northwind. "
        "Tente uma destas perguntas:\n"
        "- Quantos clientes temos?\n"
        "- Quantos colaboradores estão cadastrados?\n"
        "- Qual o total de pedidos?\n"
        "- Mostre os produtos com maior estoque\n"
        "- Me dê uma visão geral dos clientes"
    ),
    "unit_label": "unidades",
}

VALIDATION_MESSAGES_BY_TYPE_PT = {
    "string_too_short": "A pergunta deve ter pelo menos 5 caracteres.",
    "string_too_long": "A pergunta deve ter no máximo 500 caracteres.",
    "extra_forbidden": "Um campo inesperado foi enviado no corpo da requisição.",
}

VALIDATION_MESSAGES_BY_CONTENT_PT = {
    "cannot be blank": "A pergunta não pode estar em branco.",
    "too many consecutive question marks": "A pergunta contém pontos de interrogação em excesso.",
}

VALIDATION_DEFAULT_MESSAGE_PT = "Valor inválido na requisição."
VALIDATION_PAYLOAD_MESSAGE_PT = "Payload inválido. Revise os campos e tente novamente."
