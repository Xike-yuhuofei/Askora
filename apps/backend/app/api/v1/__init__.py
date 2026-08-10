"""
v1 API 路由包 (EXEC-048: No-Auth Mode)

Authentication routes are no longer exported for production no-auth mode.
Legacy auth functionality is preserved in auth.py but not registered.
"""

from app.api.v1.book_learning import router as book_learning_router
from app.api.v1.data_control import router as data_control_router
from app.api.v1.dialog import router as dialog_router
from app.api.v1.documents import router as documents_router
from app.api.v1.goals import router as goals_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.orchestrator import router as orchestrator_router
from app.api.v1.recovery import router as recovery_router
from app.api.v1.users import router as users_router
from app.api.v1.workspace import router as workspace_router
from app.api.v1.ws import router as ws_router

__all__ = [
    "book_learning_router",
    "data_control_router",
    "dialog_router",
    "users_router",
    "orchestrator_router",
    "onboarding_router",
    "recovery_router",
    "documents_router",
    "goals_router",
    "ws_router",
    "workspace_router",
]
