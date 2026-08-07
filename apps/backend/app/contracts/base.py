"""公共合同的基础类型与校验规则。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class ContractModel(BaseModel):
    """严格、不可变的跨系统公共合同基类。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("*", mode="after")
    @classmethod
    def require_timezone_aware_datetimes(cls, value: Any) -> Any:
        """DOMAIN-004：公共合同中的时间必须携带时区。"""
        if isinstance(value, datetime) and value.utcoffset() is None:
            raise ValueError("datetime must include a timezone offset")
        return value
