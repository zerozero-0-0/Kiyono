"""LLMOコンテンツジェネレーターのFastAPIアプリケーションエントリポイント。"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas import (
    ErrorResponse,
    GenerateArticleRequest,
    GenerateArticleResponse,
    GenerateTitlesRequest,
    GenerateTitlesResponse,
    ValidationReport,
)
from app.services.article_generator import ArticleGenerationInput, ArticleGenerator
from app.services.llm_client import get_llm_client
from app.services.llmo_validator import LLMOValidator
from app.services.title_generator import TitleGenerationInput, TitleGenerationService


class HealthResponse(BaseModel):
    """ヘルスチェックエンドポイントのレスポンスモデル。"""

    status: str = Field(..., description="Service status")
    app: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")


APP_TITLE = "LLMO Content Generator API"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = (
    "Backend API for generating LLMO-optimized titles and articles for the internship project."
)

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["system"],
)
def health() -> HealthResponse:
    """サービスの稼働状況と基本的なアプリケーションのメタデータを返します。"""
    return HealthResponse(
        status="ok",
        app=APP_TITLE,
        version=APP_VERSION,
    )


@app.post(
    "/generate/titles",
    response_model=GenerateTitlesResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Generate LLMO title candidates",
    tags=["generation"],
)
async def generate_titles(request: GenerateTitlesRequest) -> GenerateTitlesResponse:
    """LLMに最適化された複数のタイトル候補を生成します。

    このエンドポイントは、プロバイダに依存しないテキスト生成サービスを使用して、
    キーワードと概要に基づいたタイトルを提案します。
    """
    settings = get_settings()
    llm_client = get_llm_client(provider=settings.llm_provider)

    service = TitleGenerationService(
        llm_client=llm_client,
        temperature=settings.temperature,
        max_output_tokens=settings.max_output_tokens,
    )

    input_payload = TitleGenerationInput(
        keyword=request.keyword,
        brief=request.brief,
        n_titles=request.n_titles,
    )

    try:
        result = await service.generate(input_payload)
        return GenerateTitlesResponse(
            titles=result.titles,
            rationale=result.rationale,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@app.post(
    "/generate/article",
    response_model=GenerateArticleResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Generate LLMO structured article",
    tags=["generation"],
)
async def generate_article(request: GenerateArticleRequest) -> GenerateArticleResponse:
    """選択されたタイトルから完全なMarkdown記事を生成します。

    生成はLLMOのフォーマット規則によって制約されます。レスポンスには、
    生成されたMarkdownと、LLMO基準に対する構造化されたバリデーションレポートの両方が含まれます。
    """
    settings = get_settings()
    llm_client = get_llm_client(provider=settings.llm_provider)

    # 同期的なLLMClientをArticleGeneratorでラップします。
    # スタブは純粋に同期的なCPUバウンドのロジックであるため、高速です。
    generator = ArticleGenerator(llm_client=llm_client, model_name=settings.llm_model)
    validator = LLMOValidator()

    input_payload = ArticleGenerationInput(
        selected_title=request.selected_title,
        keyword=request.keyword,
        brief=request.brief,
        audience=request.audience,
        tone=request.tone,
    )

    try:
        result = generator.generate(input_payload)

        # 生成されたMarkdownを検証する
        raw_report = validator.validate(result.markdown_article)

        # 辞書がPydanticの期待値と安全に一致することを確認する
        validation_report = ValidationReport.model_validate(raw_report)

        return GenerateArticleResponse(
            markdown_article=result.markdown_article,
            validation_report=validation_report,
            json_ld=None,  # MVPではまだ未実装
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
