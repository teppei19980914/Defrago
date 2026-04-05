"""共通テンプレートエンジン.

全ルーターが共有するJinja2Templatesインスタンスを提供する。
labels.jsonのラベルをグローバル変数として全テンプレートに注入する。
"""

from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from study_python.gtd.web.labels import load_labels


_TEMPLATE_DIR = str(Path(__file__).parent / "templates")

templates = Jinja2Templates(directory=_TEMPLATE_DIR)
templates.env.globals["labels"] = load_labels()
