"""Container runtime path contracts."""

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def test_container_virtualenv_is_built_at_its_final_runtime_path() -> None:
    """Copied console scripts must not retain a missing /build interpreter."""

    dockerfile = (BACKEND / "Dockerfile").read_text()

    assert "ENV UV_PROJECT_ENVIRONMENT=/app/.venv" in dockerfile
    assert "COPY --from=builder /app/.venv /app/.venv" in dockerfile
    assert "COPY --from=builder /build/.venv /app/.venv" not in dockerfile
