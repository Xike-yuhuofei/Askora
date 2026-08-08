"""
初始化测试数据脚本（原生 SQL 版本）
创建个人用户测试账号
"""

import asyncio
import hashlib
import hmac
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.core.config import settings
from app.core.database import close_db, get_engine, init_db
from app.core.encryption import encrypt_pii
from app.services.auth.token_service import hash_password


def _phone_lookup_hash(phone: str) -> str:
    """为手机号生成不可逆、可查询的 HMAC 盲索引。"""
    return hmac.new(
        settings.kek_master_key.encode(),
        phone.encode(),
        hashlib.sha256,
    ).hexdigest()


async def main():
    await init_db()
    engine = get_engine()

    async with engine.begin() as conn:
        # 检查测试账号是否存在
        result = await conn.execute(text("SELECT id FROM users WHERE id = 'test-user-001'"))
        user_exists = result.fetchone() is not None

        if not user_exists:
            # 插入测试用户
            await conn.execute(
                text("""
                    INSERT INTO users (id, role, status, phone_encrypted, phone_hash, password_hash, pseudonym_id, is_verified)
                    VALUES (:id, cast(:role as userrole), cast(:status as userstatus), :phone, :phone_hash, :pwd, :pseudo, :verified)
                """),
                {
                    "id": "test-user-001",
                    "role": "USER",
                    "status": "ACTIVE",
                    "phone": encrypt_pii("15967954989"),
                    "phone_hash": _phone_lookup_hash("15967954989"),
                    "pwd": hash_password("asdf1234."),
                    "pseudo": "user_pseudo_001",
                    "verified": True,
                },
            )

            # 插入用户画像
            mastery = json.dumps(
                {
                    "math": {"mastery": 0.65, "kp_count": 120, "mastered_count": 78},
                    "chinese": {"mastery": 0.72, "kp_count": 100, "mastered_count": 72},
                    "english": {"mastery": 0.58, "kp_count": 90, "mastered_count": 52},
                    "physics": {"mastery": 0.45, "kp_count": 80, "mastered_count": 36},
                }
            )
            meta = json.dumps(
                {
                    "planning_ability": 0.6,
                    "monitoring_ability": 0.55,
                    "evaluation_ability": 0.5,
                    "reflection_quality": 0.65,
                }
            )
            affective = json.dumps(
                {
                    "engagement_level": 0.75,
                    "frustration_level": 0.2,
                    "confidence_level": 0.6,
                }
            )
            fav = json.dumps(["math", "chinese"])

            await conn.execute(
                text("""
                    INSERT INTO user_profiles (id, pseudonym_id, favorite_subjects, total_sessions, total_learning_minutes, streak_days, skills_mastered, mastery_summary, metacognition, affective, grade_level)
                    VALUES (:id, :pseudo, cast(:fav as jsonb), :sessions, :minutes, :streak, :skills, cast(:mastery as jsonb), cast(:meta as jsonb), cast(:affective as jsonb), :grade)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "pseudo": "user_pseudo_001",
                    "fav": fav,
                    "sessions": 42,
                    "minutes": 1260,
                    "streak": 7,
                    "skills": 23,
                    "mastery": mastery,
                    "meta": meta,
                    "affective": affective,
                    "grade": "高中一年级",
                },
            )

            print("  已创建测试账号: 15967954989 / asdf1234.")
        else:
            print("  测试账号已存在: test-user-001")

    await close_db()
    print("\n测试数据初始化完成！")
    print("测试账号：15967954989 / asdf1234.")


if __name__ == "__main__":
    asyncio.run(main())
