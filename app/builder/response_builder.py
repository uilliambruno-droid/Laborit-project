class ResponseBuilder:
    def build(
        self,
        message: str,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {"message": message}
        if metadata is not None:
            payload["metadata"] = metadata
        return payload
