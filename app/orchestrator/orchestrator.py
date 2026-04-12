from app.builder.response_builder import ResponseBuilder
from app.services.data_service import DataService
from app.services.llm_service import LLMService
from app.services.query_service import QueryService


class Orchestrator:
    def __init__(self) -> None:
        self.query_service = QueryService()
        self.data_service = DataService()
        self.llm_service = LLMService()
        self.response_builder = ResponseBuilder()

    def run(self, user_input: str) -> dict[str, str]:
        query = self.query_service.build_query(user_input)
        data = self.data_service.fetch_data(query)
        generated_text = self.llm_service.generate_text(user_input, data)
        return self.response_builder.build(generated_text)
