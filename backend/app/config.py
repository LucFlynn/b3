from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://epi:epi_dev_password@postgres:5432/epi"
    database_url_sync: str = "postgresql://epi:epi_dev_password@postgres:5432/epi"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    fernet_key: str = "ZmVybmV0LWRldi1rZXktMzItYnl0ZXMtbG9uZw=="
    api_key_salt: str = "dev-api-key-salt"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Server
    port: int = 8000

    # External services
    mock_server_url: str = "http://mocks:8001"
    email_validation_url: str = ""
    phone_validation_url: str = ""
    abstractapi_email_key: str = ""
    abstractapi_phone_key: str = ""
    abstractapi_ip_key: str = ""
    google_ads_developer_token: str = ""
    google_ads_login_customer_id: str = ""
    google_ads_refresh_token: str = ""
    meta_ads_access_token: str = ""

    # Email notifications (Resend)
    resend_api_key: str = ""
    notification_email: str = ""
    notification_from_email: str = "onboarding@resend.dev"

    # OAuth
    google_client_id: str = "mock-google-client-id"
    google_client_secret: str = "mock-google-client-secret"
    google_redirect_uri: str = "http://localhost:3000/onboarding/google/callback"
    meta_client_id: str = "mock-meta-client-id"
    meta_client_secret: str = "mock-meta-client-secret"
    meta_redirect_uri: str = "http://localhost:3000/onboarding/meta/callback"

    # Slack
    slack_bot_token: str = "xoxb-mock-slack-bot-token"
    slack_app_token: str = "xapp-mock-slack-app-token"
    slack_signing_secret: str = "mock-slack-signing-secret"

    # Anthropic
    anthropic_api_key: str = "mock-anthropic-api-key"

    # CORS
    allowed_origins: str = "*"

    # Rate limiting
    rate_limit_per_hour: int = 1000

    # Backend
    backend_url: str = "http://backend:8000"

    model_config = {"env_file": ".env", "extra": "ignore"}

    # ── dangerous defaults that must be overridden in production ──
    _DANGEROUS_DEFAULTS = {
        "secret_key": "dev-secret-key-change-in-production",
        "api_key_salt": "dev-api-key-salt",
        "fernet_key": "ZmVybmV0LWRldi1rZXktMzItYnl0ZXMtbG9uZw==",
    }

    @property
    def is_production(self) -> bool:
        """True when connected to a known cloud database (e.g. Neon, Supabase, RDS)."""
        db = self.database_url.lower()
        _CLOUD_HOSTS = ("neon.tech", "supabase.co", "rds.amazonaws.com", "cloud.google.com")
        return any(host in db for host in _CLOUD_HOSTS)

    def validate_production_config(self) -> None:
        """Raise on startup if production DB is used with dev-default secrets."""
        if not self.is_production:
            return
        violations = []
        for field, default_val in self._DANGEROUS_DEFAULTS.items():
            if getattr(self, field) == default_val:
                violations.append(field.upper())
        if violations:
            raise RuntimeError(
                f"PRODUCTION DATABASE detected but these env vars still have "
                f"dangerous defaults: {', '.join(violations)}. "
                f"Set real values before deploying."
            )


settings = Settings()
