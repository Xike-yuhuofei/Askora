"""
初始化测试数据脚本（原生 SQL 版本）
创建家长测试账号和儿童测试账号
"""

import asyncio
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.core.database import close_db, get_engine, init_db
from app.core.encryption import encrypt_pii
from app.services.auth.token_service import hash_password


async def main():
    await init_db()
    engine = get_engine()

    async with engine.begin() as conn:
        # 检查家长账号是否存在
        result = await conn.execute(text("SELECT id FROM users WHERE id = 'test-parent-001'"))
        parent_exists = result.fetchone() is not None

        if not parent_exists:
            # 插入家长用户
            await conn.execute(
                text("""
                    INSERT INTO users (id, role, status, phone_encrypted, password_hash, pseudonym_id, is_verified)
                    VALUES (:id, cast(:role as userrole), cast(:status as userstatus), :phone, :pwd, :pseudo, :verified)
                """),
                {
                    "id": "test-parent-001",
                    "role": "PARENT",
                    "status": "ACTIVE",
                    "phone": encrypt_pii("13800008888"),
                    "pwd": hash_password("Demo@123456"),
                    "pseudo": "parent_pseudo_001",
                    "verified": True,
                },
            )

            # 插入家长画像 - 使用 cast 避免冒号冲突
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
                    "pseudo": "parent_pseudo_001",
                    "fav": fav,
                    "sessions": 42,
                    "minutes": 1260,
                    "streak": 7,
                    "skills": 23,
                    "mastery": mastery,
                    "meta": meta,
                    "affective": affective,
                    "grade": None,
                },
            )

            # 插入同意记录
            await conn.execute(
                text("""
                    INSERT INTO consent_records (id, user_id, consent_type, status, consent_version, consent_text, action_method, context)
                    VALUES (:id, :uid, cast(:ctype as consenttype), cast(:status as consentstatus), :version, :text, :method, cast(:ctx as jsonb))
                """),
                {
                    "id": str(uuid.uuid4()),
                    "uid": "test-parent-001",
                    "ctype": "PRIVACY_POLICY",
                    "status": "GRANTED",
                    "version": "1.0",
                    "text": "用户同意隐私政策",
                    "method": "button_click",
                    "ctx": json.dumps({"ip": "127.0.0.1", "user_agent": "test-init-script"}),
                },
            )

            print("  已创建家长账号: 13800008888 / Demo@123456")
        else:
            print("  家长账号已存在: test-parent-001")

        # 检查儿童账号是否存在
        result = await conn.execute(text("SELECT id FROM users WHERE id = 'test-child-001'"))
        child_exists = result.fetchone() is not None

        if not child_exists:
            # 插入儿童用户
            await conn.execute(
                text("""
                    INSERT INTO users (id, role, status, parent_id, pseudonym_id, is_verified)
                    VALUES (:id, cast(:role as userrole), cast(:status as userstatus), :pid, :pseudo, :verified)
                """),
                {
                    "id": "test-child-001",
                    "role": "CHILD",
                    "status": "ACTIVE",
                    "pid": "test-parent-001",
                    "pseudo": "child_pseudo_001",
                    "verified": True,
                },
            )

            # 插入儿童画像
            mastery = json.dumps(
                {
                    "math": {"mastery": 0.55, "kp_count": 60, "mastered_count": 33},
                    "chinese": {"mastery": 0.6, "kp_count": 50, "mastered_count": 30},
                }
            )
            meta = json.dumps(
                {
                    "planning_ability": 0.45,
                    "monitoring_ability": 0.4,
                    "evaluation_ability": 0.35,
                    "reflection_quality": 0.5,
                }
            )
            affective = json.dumps(
                {
                    "engagement_level": 0.8,
                    "frustration_level": 0.15,
                    "confidence_level": 0.55,
                }
            )
            fav = json.dumps(["math", "science"])

            await conn.execute(
                text("""
                    INSERT INTO user_profiles (id, pseudonym_id, favorite_subjects, total_sessions, total_learning_minutes, streak_days, skills_mastered, mastery_summary, metacognition, affective, grade_level)
                    VALUES (:id, :pseudo, cast(:fav as jsonb), :sessions, :minutes, :streak, :skills, cast(:mastery as jsonb), cast(:meta as jsonb), cast(:affective as jsonb), :grade)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "pseudo": "child_pseudo_001",
                    "fav": fav,
                    "sessions": 15,
                    "minutes": 450,
                    "streak": 3,
                    "skills": 12,
                    "mastery": mastery,
                    "meta": meta,
                    "affective": affective,
                    "grade": "小学五年级",
                },
            )

            # 插入儿童扩展信息
            allowed = json.dumps(["math", "chinese", "english"])
            blocked = json.dumps([])
            goals = json.dumps({"math": "期末考到 90 分以上"})
            summary = json.dumps({"last_week_sessions": 5, "total_minutes": 120})

            await conn.execute(
                text("""
                    INSERT INTO child_profiles (id, child_pseudonym_id, daily_time_limit, allowed_subjects, blocked_keywords, learning_goals, learning_summary)
                    VALUES (:id, :pseudo, :limit, cast(:allowed as jsonb), cast(:blocked as jsonb), cast(:goals as jsonb), cast(:summary as jsonb))
                """),
                {
                    "id": str(uuid.uuid4()),
                    "pseudo": "child_pseudo_001",
                    "limit": 45,
                    "allowed": allowed,
                    "blocked": blocked,
                    "goals": goals,
                    "summary": summary,
                },
            )

            # 插入家长-子女关系
            await conn.execute(
                text("""
                    INSERT INTO parent_child_relations (id, parent_id, child_id, relation_type, is_guardian_consent_given, can_view_dialogs, can_view_assessments, can_manage_account)
                    VALUES (:id, :pid, :cid, :rtype, :consent, :dialogs, :assessments, :manage)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "pid": "test-parent-001",
                    "cid": "test-child-001",
                    "rtype": "father",
                    "consent": True,
                    "dialogs": True,
                    "assessments": True,
                    "manage": True,
                },
            )

            # 插入家长同意记录
            await conn.execute(
                text("""
                    INSERT INTO consent_records (id, user_id, consent_type, status, consent_version, consent_text, action_method, context, guardian_user_id, guardian_verification_method)
                    VALUES (:id, :uid, cast(:ctype as consenttype), cast(:status as consentstatus), :version, :text, :method, cast(:ctx as jsonb), :gid, :gmethod)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "uid": "test-child-001",
                    "ctype": "GUARDIAN_CONSENT",
                    "status": "GRANTED",
                    "version": "1.0",
                    "text": "监护人同意未成年人使用服务",
                    "method": "guardian_verified",
                    "ctx": json.dumps({"ip": "127.0.0.1", "user_agent": "test-init-script"}),
                    "gid": "test-parent-001",
                    "gmethod": "sms",
                },
            )

            print("  已创建儿童账号: child_pseudo_001")
        else:
            print("  儿童账号已存在: test-child-001")

    await close_db()
    print("\n测试数据初始化完成！")
    print("家长账号：13800008888 / Demo@123456")
    print("儿童账号：child_pseudo_001（家长授权）")


if __name__ == "__main__":
    asyncio.run(main())
