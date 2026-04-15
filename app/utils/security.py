import os
from typing import Annotated

from fastapi import Header, HTTPException, status

API_KEY_HEADER = "X-API-Key"


def get_expected_api_key() -> str | None:
    value = os.getenv("API_KEY", "").strip()
    return value or None


def require_api_key(
    x_api_key: Annotated[str | None, Header(alias=API_KEY_HEADER)] = None,
) -> None:
    expected = get_expected_api_key()
    if expected is None:
        return

    if x_api_key == expected:
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "message": "Unauthorized request: invalid or missing API key.",
            "message_pt": "Requisição não autorizada: API key ausente ou inválida.",
        },
    )
