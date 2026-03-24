"""Web版エントリポイント."""

from __future__ import annotations


def main() -> None:
    """uvicornでWebサーバーを起動する."""
    import uvicorn

    uvicorn.run(
        "study_python.gtd.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
