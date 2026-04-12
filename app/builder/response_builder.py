class ResponseBuilder:
    def build(self, message: str) -> dict[str, str]:
        return {"message": message}
