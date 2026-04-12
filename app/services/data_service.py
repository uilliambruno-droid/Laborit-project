class DataService:
    def fetch_data(self, query: str) -> dict[str, str]:
        return {"query": query, "source": "pending_database_integration"}
