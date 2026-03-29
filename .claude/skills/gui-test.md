---
name: gui-test
description: GUIアプリケーションのテスト方針。GUI/ロジック分離のアーキテクチャ原則、実装例、テスト例を含む。
---

# GUIテスト方針

GUIアプリケーションもユニットテストの対象とする。**GUIとロジックを分離**し、ロジック部分は必ずテストを作成すること。

## アーキテクチャ原則

GUIコードは以下の構造で実装する：

```
┌─────────────────────────────────────────┐
│           GUI Layer (View)              │
│  - ウィジェット配置                      │
│  - イベントハンドラ                      │
│  - 表示更新                              │
└─────────────────────────────────────────┘
                    ↓ 呼び出し
┌─────────────────────────────────────────┐
│         Logic Layer (Controller)         │
│  - ビジネスロジック                      │
│  - データ処理                            │
│  - バリデーション                        │
│  ※ このレイヤーをユニットテスト対象     │
└─────────────────────────────────────────┘
                    ↓ 呼び出し
┌─────────────────────────────────────────┐
│          Data Layer (Model)              │
│  - データアクセス                        │
│  - 永続化処理                            │
└─────────────────────────────────────────┘
```

## GUIロジック分離の実装例

```python
# src/study_python/gui/calculator_logic.py
# ロジック部分（テスト対象）

class CalculatorLogic:
    """計算機のビジネスロジック。"""

    def __init__(self) -> None:
        self.current_value: float = 0
        self.history: list[str] = []

    def add(self, value: float) -> float:
        """値を加算する。"""
        self.current_value += value
        self.history.append(f"+ {value}")
        return self.current_value

    def subtract(self, value: float) -> float:
        """値を減算する。"""
        self.current_value -= value
        self.history.append(f"- {value}")
        return self.current_value

    def clear(self) -> None:
        """リセットする。"""
        self.current_value = 0
        self.history.clear()

    def validate_input(self, value: str) -> float:
        """入力値を検証する。

        Raises:
            ValueError: 数値に変換できない場合。
        """
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Invalid number: {value}")
```

```python
# src/study_python/gui/calculator_gui.py
# GUI部分（ロジックを呼び出すのみ）

import tkinter as tk
from study_python.gui.calculator_logic import CalculatorLogic


class CalculatorGUI:
    """計算機のGUI。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.logic = CalculatorLogic()  # ロジックを注入
        self._setup_widgets()

    def _setup_widgets(self) -> None:
        """ウィジェットを配置する。"""
        self.entry = tk.Entry(self.root)
        self.entry.pack()

        self.add_button = tk.Button(
            self.root, text="+", command=self._on_add_click
        )
        self.add_button.pack()

        self.result_label = tk.Label(self.root, text="0")
        self.result_label.pack()

    def _on_add_click(self) -> None:
        """加算ボタンのクリックハンドラ。"""
        try:
            value = self.logic.validate_input(self.entry.get())
            result = self.logic.add(value)
            self.result_label.config(text=str(result))
        except ValueError as e:
            self.result_label.config(text=f"Error: {e}")
```

## GUIロジックのテスト例

```python
# tests/gui/test_calculator_logic.py
import pytest
from study_python.gui.calculator_logic import CalculatorLogic


class TestCalculatorLogic:
    """CalculatorLogicのテスト。"""

    def test_add_positive_value(self):
        logic = CalculatorLogic()
        result = logic.add(5)
        assert result == 5
        assert logic.current_value == 5

    def test_add_multiple_values(self):
        logic = CalculatorLogic()
        logic.add(5)
        result = logic.add(3)
        assert result == 8

    def test_subtract(self):
        logic = CalculatorLogic()
        logic.add(10)
        result = logic.subtract(3)
        assert result == 7

    def test_clear(self):
        logic = CalculatorLogic()
        logic.add(10)
        logic.clear()
        assert logic.current_value == 0
        assert logic.history == []

    def test_validate_input_valid(self):
        logic = CalculatorLogic()
        assert logic.validate_input("123") == 123.0
        assert logic.validate_input("45.67") == 45.67
        assert logic.validate_input("-10") == -10.0

    def test_validate_input_invalid(self):
        logic = CalculatorLogic()
        with pytest.raises(ValueError, match="Invalid number"):
            logic.validate_input("abc")

    def test_history_tracking(self):
        logic = CalculatorLogic()
        logic.add(5)
        logic.subtract(2)
        assert logic.history == ["+ 5", "- 2"]
```

## GUIフレームワーク別のテスト方法

| フレームワーク | テストライブラリ | 用途 |
|---------------|-----------------|------|
| Tkinter | `unittest.mock` | イベントのモック |
| PyQt/PySide | `pytest-qt` | Qtウィジェットのテスト |
| Kivy | `pytest` + モック | イベント・状態のテスト |
| wxPython | `unittest.mock` | イベントのモック |

## pytest-qt を使用したGUIテスト例（PyQt/PySide）

```python
# tests/gui/test_calculator_gui_qt.py
import pytest
from pytestqt.qtbot import QtBot
from PySide6.QtCore import Qt
from study_python.gui.calculator_gui_qt import CalculatorWindow


@pytest.fixture
def calculator(qtbot: QtBot) -> CalculatorWindow:
    window = CalculatorWindow()
    qtbot.addWidget(window)
    return window


def test_add_button_click(calculator: CalculatorWindow, qtbot: QtBot):
    calculator.input_field.setText("5")
    qtbot.mouseClick(calculator.add_button, Qt.LeftButton)
    assert calculator.result_label.text() == "5"


def test_invalid_input_shows_error(calculator: CalculatorWindow, qtbot: QtBot):
    calculator.input_field.setText("abc")
    qtbot.mouseClick(calculator.add_button, Qt.LeftButton)
    assert "Error" in calculator.result_label.text()
```

## テストディレクトリ構成

```
tests/
├── conftest.py              # 共通フィクスチャ
├── test_calculator.py       # 通常のユニットテスト
└── gui/                     # GUIテスト専用ディレクトリ
    ├── __init__.py
    ├── conftest.py          # GUI用フィクスチャ
    ├── test_calculator_logic.py   # ロジックのテスト
    └── test_calculator_gui.py     # GUI統合テスト（オプション）
```

## GUIテストのルール

1. **ロジック分離必須**: GUIからビジネスロジックを分離する
2. **ロジックは100%カバレッジ**: 分離したロジックは通常のユニットテスト対象
3. **GUI層は最小限**: GUI層はロジック呼び出しと表示更新のみ
4. **依存性注入**: ロジッククラスはGUIクラスに注入可能にする
5. **モックの活用**: 外部依存はモックで置き換える

## 禁止事項

- GUIクラス内にビジネスロジックを直接記述すること
- ロジック部分のテストを省略すること
- GUIイベントハンドラ内で複雑な処理を行うこと
