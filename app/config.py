"""型付き設定を使用したアプリケーション設定。

このモジュールは、プロジェクトの環境駆動型設定を一元管理します。
値は `.env`（存在する場合）から読み込まれ、
実際の環境変数によって上書きされる可能性があります。
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """型付きアプリケーション設定。

    属性:
        app_env: 実行環境名。
        log_level: ログの詳細レベル。
        host: APIサーバーのホストアドレス。
        port: APIサーバーのポート。
        llm_provider: アクティブなLLMプロバイダの識別子。
        llm_model: 選択されたプロバイダで使用されるモデル名。
        gemini_api_key: GeminiのAPIキー。
        openai_api_key: OpenAIのAPIキー。
        anthropic_api_key: AnthropicのAPIキー。
        request_timeout_seconds: 外部LLMリクエストのタイムアウト。
        max_titles: 生成されるタイトル数の上限。
        default_titles: 指定がない場合のデフォルトのタイトル数。
        temperature: 生成の温度パラメータ（temperature）。
        max_output_tokens: モデル出力の最大トークン数。
    """

    model_config = SettingsConfigDict(  # pyright: ignore[reportUnannotatedClassAttribute]
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)

    llm_provider: Literal["gemini", "openai", "anthropic"] = "gemini"
    llm_model: str = "gemini-2.5-flash"

    gemini_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None

    request_timeout_seconds: int = Field(default=60, ge=1, le=300)
    max_titles: int = Field(default=10, ge=1, le=20)
    default_titles: int = Field(default=8, ge=1, le=20)
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=8000, ge=64, le=8192)

    @property
    def provider_api_key(self) -> SecretStr | None:
        """現在選択されているプロバイダのAPIキーを返します。"""
        if self.llm_provider == "gemini":
            return self.gemini_api_key
        if self.llm_provider == "openai":
            return self.openai_api_key
        if self.llm_provider == "anthropic":
            return self.anthropic_api_key
        return None

    @property
    def provider_api_key_value(self) -> str | None:
        """選択されたプロバイダのプレーンなAPIキー文字列を返します。

        戻り値:
            プレーン文字列としてのAPIキー。設定されていない場合は `None`。
        """
        key = self.provider_api_key
        return key.get_secret_value() if key is not None else None

    def validate_runtime_constraints(self) -> None:
        """フィールド間の実行時制約を検証します。

        例外:
            ValueError: 設定の組み合わせが無効な場合。
        """
        if self.default_titles > self.max_titles:
            raise ValueError("default_titles must be less than or equal to max_titles.")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """キャッシュされたアプリケーション設定インスタンスを返します。

    戻り値:
        シングルトンのようなキャッシュされた `Settings` オブジェクト。
    """
    settings = Settings()
    settings.validate_runtime_constraints()
    return settings
