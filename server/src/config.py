from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    env: str = "development"

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    default_llm: str = "claude"  # "claude" or "openai"

    # LangSmith (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "aax-exchange"

    # Firebase / Firestore
    google_cloud_project: str = ""
    firestore_database: str = "(default)"

    # GCS
    gcs_bucket_name: str = "aax-assets"

    # Agent auth
    agent_api_key_prefix: str = "aax_sk_"

    model_config = {"env_prefix": "AAX_", "env_file": ".env"}


settings = Settings()
