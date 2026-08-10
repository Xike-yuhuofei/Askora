"""
应用配置 - 基于 pydantic-settings 的类型安全配置
精简版：移除了合规、防沉迷、审核等非个人用户功能配置

支持从环境变量与 .env 文件加载配置，生产环境强制校验密钥强度。
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(str, Enum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(str, Enum):
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
    DOUBAO = "doubao"
    ZHIPU = "zhipu"


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 基础配置
    app_env: AppEnv = AppEnv.DEVELOPMENT
    app_name: str = "socratic-learning-backend"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    private_app: bool = True
    enable_orchestrator_debug_api: bool = False
    # 开发/本地调试：允许免登录直接进入系统（仅非生产环境生效，默认关闭）
    enable_dev_auto_login: bool = False
    cors_allowed_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"
    )
    websocket_allowed_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173,null,file://"
    )

    # 数据库
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/socratic_learning"
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    redis_pool_size: int = 50

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    # 会话空闲超时（分钟）：超过此时长未活跃的会话不计入并发上限
    session_idle_timeout_minutes: int = 30

    # 密钥管理（简化版）
    kek_master_key: str = "change-me-kek-key-at-least-32-bytes-long"

    # LLM
    llm_default_provider: LLMProvider = LLMProvider.QWEN
    llm_qwen_api_key: str = ""
    llm_qwen_model: str = "qwen-turbo"
    llm_deepseek_api_key: str = ""
    llm_deepseek_model: str = "deepseek-chat"
    llm_doubao_api_key: str = ""
    llm_doubao_model: str = "doubao-pro-32k"
    llm_zhipu_api_key: str = ""
    llm_zhipu_model: str = "glm-4.7-flash"
    llm_zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    llm_zhipu_thinking_enabled: bool = False
    llm_math_provider: LLMProvider = LLMProvider.DEEPSEEK
    embedding_provider: str = "qwen"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    llm_timeout: int = 30

    # 日志
    log_level: str = "INFO"
    log_format: str = "json"

    # 监控
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # 限流
    rate_limit_user_per_minute: int = 20
    rate_limit_ip_per_minute: int = 1000

    # 本地文件存储（文档上传）
    local_storage_enabled: bool = True
    local_storage_base_path: str = "./data/documents"
    local_storage_max_file_size_mb: int = 50
    local_storage_max_total_size_gb: int = 2
    local_storage_chunk_min_tokens: int = 200
    local_storage_chunk_max_tokens: int = 800
    local_storage_archive_max_entries: int = 5000
    local_storage_archive_max_entry_size_mb: int = 50
    local_storage_archive_max_uncompressed_size_mb: int = 250
    local_storage_archive_max_compression_ratio: float = 100.0

    # Embedding 向量服务
    embedding_api_key: str = ""
    embedding_api_base: str = "https://dashscope.aliyuncs.com"
    embedding_model: str = "text-embedding-v2"
    embedding_dimension: int = 1536

    # Worker 任务队列
    worker_enabled: bool = True
    worker_max_concurrent: int = 5
    worker_poll_interval: float = 1.0

    # 账号删除与数据库外恢复屏障
    privacy_restore_barrier_path: str = "./data/privacy/restore-barriers.json"
    account_deletion_poll_interval: float = 5.0
    account_deletion_max_attempts: int = 3
    account_deletion_grace_hours: float = 24.0

    @model_validator(mode="after")
    def validate_production_keys(self) -> "Settings":
        """生产环境强制校验密钥强度，防止使用默认/示例密钥"""
        if self.app_env == AppEnv.PRODUCTION:
            if not self.jwt_secret_key or self.jwt_secret_key == "change-me-in-production":
                raise ValueError("JWT_SECRET_KEY must be set to a strong value in production")
            if len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
            if not self.kek_master_key or len(self.kek_master_key) < 32:
                raise ValueError("KEK_MASTER_KEY must be at least 32 characters in production")
            if self.kek_master_key == "change-me-kek-key-at-least-32-bytes-long":
                raise ValueError("KEK_MASTER_KEY must not use the default value in production")
        if self.local_storage_chunk_min_tokens >= self.local_storage_chunk_max_tokens:
            raise ValueError(
                "LOCAL_STORAGE_CHUNK_MIN_TOKENS must be smaller than LOCAL_STORAGE_CHUNK_MAX_TOKENS"
            )
        if self.local_storage_archive_max_entries < 1:
            raise ValueError("LOCAL_STORAGE_ARCHIVE_MAX_ENTRIES must be positive")
        if self.local_storage_archive_max_entry_size_mb < 1:
            raise ValueError("LOCAL_STORAGE_ARCHIVE_MAX_ENTRY_SIZE_MB must be positive")
        if self.local_storage_archive_max_uncompressed_size_mb < 1:
            raise ValueError("LOCAL_STORAGE_ARCHIVE_MAX_UNCOMPRESSED_SIZE_MB must be positive")
        if self.local_storage_archive_max_compression_ratio <= 1:
            raise ValueError("LOCAL_STORAGE_ARCHIVE_MAX_COMPRESSION_RATIO must be greater than 1")
        if self.account_deletion_poll_interval <= 0:
            raise ValueError("ACCOUNT_DELETION_POLL_INTERVAL must be positive")
        if self.account_deletion_max_attempts < 1:
            raise ValueError("ACCOUNT_DELETION_MAX_ATTEMPTS must be positive")
        if self.account_deletion_grace_hours < 0:
            raise ValueError("ACCOUNT_DELETION_GRACE_HOURS must not be negative")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnv.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.app_env == AppEnv.DEVELOPMENT

    @property
    def is_local(self) -> bool:
        return self.app_env == AppEnv.LOCAL

    @property
    def is_test(self) -> bool:
        return self.app_env == AppEnv.TEST

    @property
    def dev_auto_login_enabled(self) -> bool:
        """开发自动登录仅在非生产环境且显式开启时可用。"""
        return self.enable_dev_auto_login and not self.is_production

    @property
    def auto_create_tables(self) -> bool:
        return self.app_env in {AppEnv.LOCAL, AppEnv.DEVELOPMENT, AppEnv.TEST}

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def websocket_origins(self) -> set[str]:
        return {
            origin.strip() for origin in self.websocket_allowed_origins.split(",") if origin.strip()
        }


settings = Settings()
