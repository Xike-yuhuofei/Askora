"""
简化版加密服务
移除了复杂的 KEK/DEK 分层密钥管理
仅保留基础的加密/解密功能，用于敏感数据保护
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """
    简化版加密服务
    使用单一密钥进行数据加密/解密
    """

    _fernet_instance: Fernet | None = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        """获取 Fernet 实例（延迟初始化）"""
        if cls._fernet_instance is None:
            # 从主密钥派生 Fernet 密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"askora_simple_encryption_salt",
                iterations=100000,
            )
            derived_key = kdf.derive(settings.kek_master_key.encode())
            fernet_key = base64.urlsafe_b64encode(derived_key)
            cls._fernet_instance = Fernet(fernet_key)
        return cls._fernet_instance

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        加密数据

        Args:
            plaintext: 明文

        Returns:
            加密后的 Base64 字符串
        """
        fernet = cls._get_fernet()
        encrypted = fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted.decode("utf-8")

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        解密数据

        Args:
            ciphertext: 加密的 Base64 字符串

        Returns:
            明文
        """
        try:
            fernet = cls._get_fernet()
            decrypted = fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted.decode("utf-8")
        except InvalidToken:
            logger.error("decryption_failed")
            raise ValueError("数据解密失败，密钥可能已变更")

    @staticmethod
    def hash_id(value: str, salt: str = "") -> str:
        """
        对 ID 类数据进行单向哈希
        """
        combined = f"{value}:{salt}:askora_hash_pepper".encode("utf-8")
        return hashlib.sha256(combined).hexdigest()[:32]

    @staticmethod
    def mask_phone(phone: str) -> str:
        """手机号脱敏"""
        if len(phone) >= 11:
            return phone[:3] + "****" + phone[7:]
        return "****"

    @staticmethod
    def mask_name(name: str) -> str:
        """姓名脱敏"""
        if len(name) <= 1:
            return name
        if len(name) == 2:
            return name[0] + "*"
        return name[0] + "*" * (len(name) - 1)

    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """身份证号脱敏"""
        if len(id_card) >= 14:
            return id_card[:6] + "********" + id_card[-4:]
        return "****"


# 便捷函数
def encrypt_value(value: str) -> str:
    """便捷加密函数"""
    return EncryptionService.encrypt(value)


def decrypt_value(ciphertext: str) -> str:
    """便捷解密函数"""
    return EncryptionService.decrypt(ciphertext)


# 兼容旧版函数名
def encrypt_pii(value: str) -> str:
    """加密 PII 数据（兼容旧版接口）"""
    return EncryptionService.encrypt(value)


def decrypt_pii(ciphertext: str) -> str:
    """解密 PII 数据（兼容旧版接口）"""
    return EncryptionService.decrypt(ciphertext)
