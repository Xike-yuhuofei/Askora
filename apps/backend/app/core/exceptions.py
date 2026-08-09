"""
统一异常定义与错误码
合规相关错误码使用 4xx 系列，业务错误使用业务码
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, status


class AppError(HTTPException):
    """应用基础异常类"""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        detail: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        category: str | None = None,
        retryable: bool = False,
        recovery: Optional[dict[str, Any]] = None,
        correlation_id: str | None = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.error_detail = detail or {}
        self.category = category or self._category_for_status(status_code)
        self.retryable = retryable
        self.recovery = recovery
        self.correlation_id = correlation_id
        super().__init__(status_code=status_code, detail=message, headers=headers)

    @staticmethod
    def _category_for_status(status_code: int) -> str:
        if status_code in {401, 403}:
            return "authorization"
        if status_code == 404:
            return "not_found"
        if status_code == 409:
            return "conflict"
        if status_code == 422:
            return "validation"
        if status_code == 429:
            return "transient"
        if status_code >= 500:
            return "internal"
        return "business"


# ========== 认证授权相关 (AUTH-xxxx) ==========


class AuthError(AppError):
    """认证基础异常"""

    pass


class InvalidTokenError(AuthError):
    """Token 无效"""

    def __init__(self, message: str = "Token 无效或已过期") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH-0001",
            message=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InsufficientPermissionsError(AuthError):
    """权限不足"""

    def __init__(self, message: str = "权限不足") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTH-0002",
            message=message,
        )


class HorizontalPrivilegeEscalationError(AuthError):
    """水平越权（IDOR）"""

    def __init__(self, resource: str = "资源") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTH-0003",
            message=f"无权访问该{resource}",
        )


class DeviceMismatchError(AuthError):
    """设备不匹配（儿童账号强化）"""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH-0004",
            message="设备指纹不匹配，请使用授权设备登录",
        )


class TooManySessionsError(AuthError):
    """并发会话超限"""

    def __init__(self, max_sessions: int = 3) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="AUTH-0005",
            message=f"并发会话数已达上限（{max_sessions}个）",
        )


class AuthenticationStateUnavailableError(AuthError):
    """认证状态存储不可用，生产环境必须拒绝放行。"""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="AUTH-0006",
            message="认证状态服务暂时不可用，请稍后重试",
            category="dependency",
            retryable=True,
        )


# ========== 合规相关 (COMP-xxxx) ==========


class ComplianceError(AppError):
    """合规基础异常"""

    pass


class ContentViolationError(ComplianceError):
    """内容违规"""

    def __init__(self, violation_type: str = "内容违规") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="COMP-0001",
            message=f"内容检测未通过：{violation_type}",
        )


class AntiAddictionTimeLimitError(ComplianceError):
    """防沉迷-时长超限"""

    def __init__(self, used_minutes: int, limit_minutes: int) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="COMP-0002",
            message="今日使用时长已达上限",
            detail={"used_minutes": used_minutes, "limit_minutes": limit_minutes},
        )


class AntiAddictionForbiddenPeriodError(ComplianceError):
    """防沉迷-禁玩时段"""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="COMP-0003",
            message="当前为禁玩时段（22:00-06:00），无法使用服务",
        )


class ConsentRequiredError(ComplianceError):
    """缺少必要同意"""

    def __init__(self, consent_type: str = "必要同意") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="COMP-0004",
            message=f"需要先授权{consent_type}才能使用服务",
        )


class GuardianConsentRequiredError(ComplianceError):
    """需要监护人同意（未成年人）"""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="COMP-0005",
            message="未成年人使用需监护人单独同意",
        )


class ModerationDegradedError(ComplianceError):
    """审核降级 - 功能受限"""

    def __init__(self, level: str = "L1") -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="COMP-0006",
            message=f"系统维护中，服务暂时受限（降级级别：{level}）",
        )


# ========== 数据相关 (DATA-xxxx) ==========


class DataError(AppError):
    """数据基础异常"""

    pass


class ResourceNotFoundError(DataError):
    """资源不存在"""

    def __init__(self, resource: str = "资源") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DATA-0001",
            message=f"{resource}不存在",
        )


class DeletionInProgressError(DataError):
    """删除进行中"""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="DATA-0002",
            message="数据删除流程进行中",
        )


class DeletionCoolingDownError(DataError):
    """删除冷静期内"""

    def __init__(self, days_remaining: int) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="DATA-0003",
            message=f"删除冷静期内（剩余 {days_remaining} 天），可撤销",
            detail={"days_remaining": days_remaining},
        )


# ========== 限流相关 (RATE-xxxx) ==========


class RateLimitError(AppError):
    """限流基础异常"""

    def __init__(self, message: str = "请求过于频繁，请稍后再试") -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE-0001",
            message=message,
            category="transient",
            retryable=True,
        )


# ========== 业务相关 (BIZ-xxxx) ==========


class BusinessError(AppError):
    """业务基础异常"""

    def __init__(
        self,
        message: str,
        error_code: str = "BIZ-0001",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: Optional[dict[str, Any]] = None,
        category: str = "business",
        retryable: bool = False,
        recovery: Optional[dict[str, Any]] = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            error_code=error_code,
            message=message,
            detail=detail,
            category=category,
            retryable=retryable,
            recovery=recovery,
            correlation_id=correlation_id,
        )


class RecoveryIssueNotFoundError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="恢复问题不存在或不可访问",
            error_code="RECOVERY_ISSUE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            category="not_found",
        )


class RecoveryActionNotAllowedError(BusinessError):
    def __init__(self, reason_code: str = "RECOVERY_ACTION_NOT_ALLOWED") -> None:
        super().__init__(
            message="当前问题不允许执行该恢复动作",
            error_code="RECOVERY_ACTION_NOT_ALLOWED",
            status_code=status.HTTP_409_CONFLICT,
            category="conflict",
            detail={"reason_code": reason_code},
        )


class RecoveryVersionConflictError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="问题状态已更新，请刷新后重试",
            error_code="CONCURRENT_VERSION_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            category="conflict",
        )


class ContentFileMissingError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="资料记录仍在，但原文件当前不可用",
            error_code="CONTENT_FILE_MISSING",
            status_code=status.HTTP_409_CONFLICT,
            category="data_integrity",
            recovery={
                "issue_ref": None,
                "retry_after_seconds": None,
                "actions": [],
            },
        )


class ContentChecksumMismatchError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="原文件完整性校验失败，未执行重试",
            error_code="DATABASE_INTEGRITY_FAILED",
            status_code=status.HTTP_409_CONFLICT,
            category="data_integrity",
        )


class ValidationInputError(BusinessError):
    """业务输入校验失败。"""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="BIZ-0002",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class SessionNotActiveError(BusinessError):
    """已结束或归档的会话不能继续写入。"""

    def __init__(self) -> None:
        super().__init__(
            message="当前会话已结束，不能继续发送消息",
            error_code="BIZ-0003",
            status_code=status.HTTP_409_CONFLICT,
        )


class ContentReinspectionNotAllowedError(BusinessError):
    """Only quarantined content may enter explicit reinspection."""

    def __init__(self) -> None:
        super().__init__(
            message="只有已隔离资料可以重新检查",
            error_code="CONTENT_REINSPECTION_NOT_ALLOWED",
            status_code=status.HTTP_409_CONFLICT,
        )


class ContentReinspectionPolicyUnchangedError(BusinessError):
    """A security rejection is not retryable under the same policy."""

    def __init__(self) -> None:
        super().__init__(
            message="当前安全检查策略没有更新，不能重复检查",
            error_code="CONTENT_REINSPECTION_POLICY_UNCHANGED",
            status_code=status.HTTP_409_CONFLICT,
        )


class ContentReinspectionChecksumMismatchError(BusinessError):
    """The stored raw asset no longer matches its immutable baseline."""

    def __init__(self) -> None:
        super().__init__(
            message="原始资料已发生变化，请重新上传",
            error_code="CONTENT_REINSPECTION_CHECKSUM_MISMATCH",
            status_code=status.HTTP_409_CONFLICT,
        )


class ContentReinspectionUnavailableError(BusinessError):
    """The durable reinspection task cannot be reused or recovered."""

    def __init__(self) -> None:
        super().__init__(
            message="重新检查任务无法继续，请重新上传资料",
            error_code="CONTENT_REINSPECTION_UNAVAILABLE",
            status_code=status.HTTP_409_CONFLICT,
        )


class LibraryMetadataVersionConflictError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="资料信息已被更新，请刷新后重试",
            error_code="LIBRARY_METADATA_VERSION_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
        )


class LibraryIdempotencyConflictError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="重复请求使用了不同内容",
            error_code="LIBRARY_IDEMPOTENCY_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
        )


class LibraryBatchScopeInvalidError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="批量操作必须明确选择 1 到 100 份资料",
            error_code="LIBRARY_BATCH_SCOPE_INVALID",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class DuplicateSuggestionNotActionableError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="重复资料建议已处理或版本已变化",
            error_code="DUPLICATE_SUGGESTION_NOT_ACTIONABLE",
            status_code=status.HTTP_409_CONFLICT,
        )


class OcrNotApplicableError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="当前资料不是可进行文字识别的 PDF",
            error_code="OCR_NOT_APPLICABLE",
            status_code=status.HTTP_409_CONFLICT,
        )


class OcrEngineUnavailableError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="本地文字识别引擎不可用",
            error_code="OCR_ENGINE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class OcrTimeoutError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="本地文字识别超时，原资料未发生变化",
            error_code="OCR_TIMEOUT",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class OcrOutputInvalidError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="本地文字识别没有产生可复核文本",
            error_code="OCR_OUTPUT_INVALID",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class OcrRunNotReadyError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="文字识别结果尚未准备好",
            error_code="OCR_RUN_NOT_READY",
            status_code=status.HTTP_409_CONFLICT,
        )


class OcrReviewVersionConflictError(BusinessError):
    def __init__(self) -> None:
        super().__init__(
            message="识别候选已被修改，请刷新后重试",
            error_code="OCR_REVIEW_VERSION_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
        )
