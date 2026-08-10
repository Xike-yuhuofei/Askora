"""
安全与合规模块
涵盖限流、输入净化、内容分类、审计追踪、数据匿名化、API 密钥管理
"""

from __future__ import annotations

import asyncio
import html
import re
import secrets
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.core.config import settings
from app.core.encryption import EncryptionService
from app.core.logging import get_logger

logger = get_logger(__name__)


# ==================== 1. 限流 (Rate Limiting) ====================


@dataclass
class TokenBucket:
    """令牌桶状态"""

    tokens: float
    max_tokens: int
    refill_rate: float
    last_refill: float


class RateLimiter:
    """
    内存令牌桶限流器

    使用令牌桶算法实现平滑限流，支持:
    - 按用户 ID 限流
    - 按 IP 限流
    - 按操作类型限流
    """

    def __init__(self) -> None:
        self._buckets: dict[str, TokenBucket] = {}

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        检查请求是否被允许

        Args:
            key: 限流键（如 user:{id}:{action} 或 ip:{ip}）
            limit: 时间窗口内的最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            True 表示允许，False 表示拒绝
        """
        now = time.time()
        refill_rate = limit / window_seconds

        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(
                tokens=float(limit),
                max_tokens=limit,
                refill_rate=refill_rate,
                last_refill=now,
            )
            self._buckets[key] = bucket

        elapsed = now - bucket.last_refill
        bucket.tokens = min(bucket.max_tokens, bucket.tokens + elapsed * bucket.refill_rate)
        bucket.last_refill = now

        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return True
        return False

    def get_remaining(self, key: str) -> int:
        """获取剩余可用令牌数"""
        bucket = self._buckets.get(key)
        if bucket is None:
            return 0
        return int(bucket.tokens)

    def reset(self, key: str) -> None:
        """重置指定键的限流状态"""
        self._buckets.pop(key, None)

    def reset_all(self) -> None:
        """重置所有限流状态"""
        self._buckets.clear()


_rate_limiter = RateLimiter()


async def check_rate_limit(user_id: str, action: str) -> bool:
    """
    检查用户操作的限流状态

    Args:
        user_id: 用户 ID
        action: 操作类型（如 dialog.send, document.upload）

    Returns:
        True 表示允许访问
    """
    key = f"user:{user_id}:{action}"
    limit = settings.rate_limit_user_per_minute
    allowed = _rate_limiter.is_allowed(key, limit=limit, window_seconds=60)
    if not allowed:
        logger.warning(
            "rate_limit_exceeded",
            user_id=user_id,
            action=action,
            limit=limit,
        )
    return allowed


async def check_ip_rate_limit(ip: str) -> bool:
    """检查 IP 级别的限流状态"""
    key = f"ip:{ip}"
    limit = settings.rate_limit_ip_per_minute
    allowed = _rate_limiter.is_allowed(key, limit=limit, window_seconds=60)
    if not allowed:
        logger.warning("ip_rate_limit_exceeded", ip=ip, limit=limit)
    return allowed


# ==================== 2. 输入净化 (Input Sanitization) ====================


_XSS_PATTERNS = [
    re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*/\s*script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<\s*iframe[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*img[^>]*on\w+\s*=", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"url\s*\(\s*[\"']?\s*javascript:", re.IGNORECASE),
]

_SQL_INJECTION_PATTERNS = [
    re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|EXECUTE)\b", re.IGNORECASE),
    re.compile(r"(--|#|;)\s"),
    re.compile(r"\bOR\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+", re.IGNORECASE),
    re.compile(r"\bAND\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+", re.IGNORECASE),
    re.compile(r"'\s*(OR|AND)\s+'[^']*'\s*=\s*'", re.IGNORECASE),
    re.compile(r";\s*(DROP|DELETE|UPDATE|INSERT)\b", re.IGNORECASE),
    re.compile(r"UNION\s+(ALL\s+)?SELECT", re.IGNORECASE),
    re.compile(r"'\s*;\s*--"),
    re.compile(r"1\s*=\s*1"),
    re.compile(r"'\s+OR\s+1\s*=\s*1", re.IGNORECASE),
    re.compile(r"\bxp_cmdshell\b", re.IGNORECASE),
    re.compile(r"\bsleep\s*\(\s*\d+\s*\)", re.IGNORECASE),
    re.compile(r"\bbenchmark\s*\(", re.IGNORECASE),
]


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    净化用户输入

    Args:
        text: 原始输入文本
        max_length: 最大长度限制

    Returns:
        净化后的文本
    """
    if not text:
        return ""

    cleaned = html.unescape(text)
    cleaned = re.sub(r"<[^>]*>", "", cleaned)
    cleaned = re.sub(r"[<>]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned


def detect_injection_attempt(text: str) -> bool:
    """
    检测是否存在注入攻击尝试

    Args:
        text: 待检测文本

    Returns:
        True 表示检测到可疑注入模式
    """
    if not text:
        return False

    for pattern in _XSS_PATTERNS:
        if pattern.search(text):
            logger.warning("xss_pattern_detected", pattern=pattern.pattern[:32])
            return True

    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning("sql_injection_pattern_detected", pattern=pattern.pattern[:32])
            return True

    return False


# ==================== 3. 内容分类 (Content Classification) ====================


class ContentCategory(str, Enum):
    EDUCATIONAL = "educational"
    PERSONAL_INFO = "personal_info"
    HARMFUL = "harmful"
    NEUTRAL = "neutral"


class RiskLevel(str, Enum):
    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"


_PII_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"1[3-9]\d{9}"), "phone"),
    (re.compile(r"\d{17}[\dXx]"), "id_card"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "email"),
    (re.compile(r"\d{6}"), "postal_code"),
    (re.compile(r"44010[0-9]\d{11}"), "bank_card"),
]

_HARMFUL_KEYWORDS: set[str] = {
    "自杀",
    "自残",
    "暴力",
    "色情",
    "赌博",
    "毒品",
    "恐怖主义",
    "极端主义",
    "歧视",
    "仇恨",
    "suicide",
    "self-harm",
    "violence",
    "pornography",
    "gambling",
    "drug",
    "terrorism",
    "extremism",
}

_EDUCATIONAL_KEYWORDS: set[str] = {
    "学习",
    "知识",
    "数学",
    "物理",
    "化学",
    "语文",
    "解题",
    "思考",
    "理解",
    "分析",
    "原理",
    "learn",
    "study",
    "knowledge",
    "math",
    "physics",
    "chemistry",
    "solve",
    "understand",
}


def classify_content(text: str) -> dict[str, str]:
    """
    对内容进行分类和风险评估

    Args:
        text: 待分类文本

    Returns:
        {
            "category": educational | personal_info | harmful | neutral,
            "risk_level": safe | warning | danger
        }
    """
    if not text:
        return {"category": ContentCategory.NEUTRAL.value, "risk_level": RiskLevel.SAFE.value}

    text_lower = text.lower()
    category = ContentCategory.NEUTRAL
    risk_level = RiskLevel.SAFE

    pii_score = 0
    for pattern, pii_type in _PII_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            pii_score += len(matches)
            if pii_type in ("id_card", "bank_card"):
                pii_score += 2

    harmful_score = sum(1 for kw in _HARMFUL_KEYWORDS if kw in text_lower)
    educational_score = sum(1 for kw in _EDUCATIONAL_KEYWORDS if kw in text_lower)

    if harmful_score >= 2:
        category = ContentCategory.HARMFUL
        risk_level = RiskLevel.DANGER
    elif harmful_score >= 1:
        category = ContentCategory.HARMFUL
        risk_level = RiskLevel.WARNING
    elif pii_score >= 3:
        category = ContentCategory.PERSONAL_INFO
        risk_level = RiskLevel.DANGER
    elif pii_score >= 1:
        category = ContentCategory.PERSONAL_INFO
        risk_level = RiskLevel.WARNING
    elif educational_score >= 1:
        category = ContentCategory.EDUCATIONAL
        risk_level = RiskLevel.SAFE

    if risk_level in (RiskLevel.WARNING, RiskLevel.DANGER):
        logger.info(
            "content_classified",
            category=category.value,
            risk_level=risk_level.value,
            text_length=len(text),
        )

    return {"category": category.value, "risk_level": risk_level.value}


# ==================== 4. 审计追踪 (Audit Trail) ====================


class AuditEventType(str, Enum):
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    SETTINGS_CHANGE = "settings_change"


@dataclass
class AuditEvent:
    """审计事件"""

    event_id: str
    event_type: str
    actor_id: str
    details: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


_AUDIT_RING_BUFFER: deque[AuditEvent] = deque(maxlen=10000)
_audit_lock = asyncio.Lock()


async def log_audit_event(
    event_type: str,
    actor_id: str,
    details: Optional[dict[str, Any]] = None,
) -> AuditEvent:
    """
    记录审计事件到内存环形缓冲区

    Args:
        event_type: 事件类型（见 AuditEventType）
        actor_id: 操作者 ID
        details: 事件详情

    Returns:
        已记录的审计事件
    """
    event_id = str(uuid.uuid4())
    event = AuditEvent(
        event_id=event_id,
        event_type=event_type,
        actor_id=actor_id,
        details=details or {},
    )

    async with _audit_lock:
        _AUDIT_RING_BUFFER.append(event)

    logger.info(
        "audit_event_logged",
        event_type=event_type,
        actor_id=actor_id,
        event_id=event_id,
    )

    return event


async def get_recent_audit_events(limit: int = 100) -> list[AuditEvent]:
    """
    获取最近的审计事件

    Args:
        limit: 返回最大数量

    Returns:
        审计事件列表（按时间倒序）
    """
    async with _audit_lock:
        events = list(_AUDIT_RING_BUFFER)
    events.reverse()
    return events[:limit]


async def get_audit_events_by_type(event_type: str, limit: int = 100) -> list[AuditEvent]:
    """按事件类型筛选审计事件"""
    async with _audit_lock:
        events = [e for e in _AUDIT_RING_BUFFER if e.event_type == event_type]
    events.reverse()
    return events[:limit]


# ==================== 5. 数据匿名化 (Data Anonymization) ====================


def generate_pseudonym_id(user_id: str) -> str:
    """
    生成确定性的伪匿名 ID

    相同 user_id 始终生成相同的伪 ID，
    不可逆，用于数据关联但不暴露真实 ID

    Args:
        user_id: 真实用户 ID

    Returns:
        伪匿名 ID
    """
    return EncryptionService.hash_id(user_id, salt="askora_pseudonym")


def anonymize_user_data(user_data: dict[str, Any]) -> dict[str, Any]:
    """
    匿名化用户数据，对 PII 字段进行假名化处理

    Args:
        user_data: 原始用户数据字典

    Returns:
        匿名化后的数据副本
    """
    if not user_data:
        return {}

    pii_fields = {"phone", "email", "id_card", "real_name", "bank_card"}
    pseudonym_fields = {"user_id", "id", "uid"}

    anonymized: dict[str, Any] = {}

    for key, value in user_data.items():
        if value is None:
            anonymized[key] = None
            continue

        if key in pseudonym_fields:
            anonymized[key] = generate_pseudonym_id(str(value))
        elif key == "phone":
            anonymized[key] = EncryptionService.mask_phone(str(value))
        elif key == "real_name" or key == "name":
            anonymized[key] = EncryptionService.mask_name(str(value))
        elif key == "id_card":
            anonymized[key] = EncryptionService.mask_id_card(str(value))
        elif key == "email":
            email_str = str(value)
            if "@" in email_str:
                local, domain = email_str.rsplit("@", 1)
                anonymized[key] = local[:2] + "***" + local[-1:] + "@" + domain
            else:
                anonymized[key] = "***"
        elif key == "bank_card":
            anonymized[key] = str(value)[:4] + " **** **** " + str(value)[-4:]
        elif key in pii_fields:
            anonymized[key] = "***"
        else:
            anonymized[key] = value

    return anonymized


# ==================== 6. API 密钥管理 (API Key Management) ====================


@dataclass
class APIKey:
    """API 密钥对象"""

    key_id: str
    user_id: str
    key_hash: str
    scopes: list[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    is_active: bool = True


_API_KEY_STORE: dict[str, APIKey] = {}
_api_key_raw_index: dict[str, str] = {}


def hash_api_key(raw_key: str) -> str:
    """
    哈希 API 密钥

    Args:
        raw_key: 原始密钥字符串

    Returns:
        哈希后的密钥
    """
    return EncryptionService.hash_id(raw_key, salt="askora_api_key")


async def create_api_key(
    user_id: str,
    scopes: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    为用户创建 API 密钥

    Args:
        user_id: 用户 ID
        scopes: 权限范围列表

    Returns:
        {
            "key_id": 密钥 ID,
            "api_key": 原始密钥（仅返回一次）,
            "scopes": 权限范围,
            "created_at": 创建时间
        }
    """
    scopes = scopes or ["read"]
    key_id = str(uuid.uuid4())
    raw_key = f"askora_{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(raw_key)

    api_key = APIKey(
        key_id=key_id,
        user_id=user_id,
        key_hash=key_hash,
        scopes=scopes,
    )

    _API_KEY_STORE[key_id] = api_key
    _api_key_raw_index[key_hash] = key_id

    logger.info(
        "api_key_created",
        user_id=user_id,
        key_id=key_id,
        scopes=scopes,
    )

    return {
        "key_id": key_id,
        "api_key": raw_key,
        "scopes": scopes,
        "created_at": api_key.created_at.isoformat(),
    }


async def validate_api_key(
    api_key: str,
) -> dict[str, Any]:
    """
    验证 API 密钥

    Args:
        api_key: 原始密钥字符串

    Returns:
        {
            "valid": 是否有效,
            "scopes": 权限范围,
            "user_id": 用户 ID,
            "key_id": 密钥 ID
        }
    """
    key_hash = hash_api_key(api_key)
    key_id = _api_key_raw_index.get(key_hash)

    if key_id is None:
        logger.warning("api_key_validation_failed", reason="key_not_found")
        return {"valid": False, "scopes": [], "user_id": "", "key_id": ""}

    api_key_obj = _API_KEY_STORE.get(key_id)
    if api_key_obj is None or not api_key_obj.is_active:
        logger.warning("api_key_validation_failed", reason="key_inactive")
        return {"valid": False, "scopes": [], "user_id": "", "key_id": ""}

    api_key_obj.last_used_at = datetime.utcnow()

    return {
        "valid": True,
        "scopes": api_key_obj.scopes,
        "user_id": api_key_obj.user_id,
        "key_id": api_key_obj.key_id,
    }


async def revoke_api_key(key_id: str) -> bool:
    """撤销 API 密钥"""
    api_key_obj = _API_KEY_STORE.get(key_id)
    if api_key_obj is None:
        return False

    api_key_obj.is_active = False
    logger.info("api_key_revoked", key_id=key_id)
    return True


async def list_user_api_keys(user_id: str) -> list[dict[str, Any]]:
    """列出用户的所有 API 密钥"""
    result = []
    for key_id, api_key_obj in _API_KEY_STORE.items():
        if api_key_obj.user_id == user_id:
            result.append(
                {
                    "key_id": key_id,
                    "scopes": api_key_obj.scopes,
                    "created_at": api_key_obj.created_at.isoformat(),
                    "last_used_at": (
                        api_key_obj.last_used_at.isoformat() if api_key_obj.last_used_at else None
                    ),
                    "is_active": api_key_obj.is_active,
                }
            )
    return result
