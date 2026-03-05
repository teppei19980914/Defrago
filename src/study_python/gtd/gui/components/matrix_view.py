"""重要度×緊急度マトリクス表示コンポーネント.

4象限のマトリクスとタスクのドットをペイントする。
"""

from __future__ import annotations

import logging
from collections import defaultdict

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget

from study_python.gtd.gui.styles import COLORS
from study_python.gtd.models import GtdItem


logger = logging.getLogger(__name__)

_MARGIN = 50
_DOT_RADIUS = 6
_LABEL_MAX_CHARS = 12
_OVERLAP_OFFSET_Y = 18


class MatrixView(QWidget):
    """重要度×緊急度の4象限マトリクスを描画するウィジェット."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: list[GtdItem] = []
        self._dot_positions: list[tuple[QPointF, GtdItem]] = []
        self._hit_areas: list[tuple[QRectF, GtdItem]] = []
        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)

    def set_items(self, items: list[GtdItem]) -> None:
        """表示するアイテムを設定する.

        Args:
            items: 重要度・緊急度が設定されたアイテムのリスト。
        """
        self._items = [
            item
            for item in items
            if item.importance is not None and item.urgency is not None
        ]
        self.update()

    def _calc_dot_positions(self, plot_w: float, plot_h: float) -> None:
        """各アイテムのドット描画座標を計算する.

        同じ（重要度, 緊急度）を持つアイテムはY方向にオフセットして散らす。
        """
        self._dot_positions = []

        groups: dict[tuple[int, int], list[GtdItem]] = defaultdict(list)
        for item in self._items:
            if item.importance is None or item.urgency is None:
                continue  # pragma: no cover
            groups[(item.importance, item.urgency)].append(item)

        for (importance, urgency), group_items in groups.items():
            nx = (urgency - 1) / 9
            ny = 1 - (importance - 1) / 9

            base_x = _MARGIN + nx * plot_w
            base_y = _MARGIN + ny * plot_h

            total = len(group_items)
            for idx, item in enumerate(group_items):
                offset_y = (idx - (total - 1) / 2) * _OVERLAP_OFFSET_Y
                pos = QPointF(base_x, base_y + offset_y)
                self._dot_positions.append((pos, item))

    @staticmethod
    def _get_dot_color(item: GtdItem) -> str:
        """アイテムの象限に応じたドット色を返す."""
        importance = item.importance or 0
        urgency = item.urgency or 0
        if importance > 5 and urgency > 5:
            return COLORS["q1_color"]
        if importance > 5:
            return COLORS["q2_color"]
        if urgency > 5:
            return COLORS["q3_color"]
        return COLORS["q4_color"]

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """マウスホバーでツールチップを表示する."""
        pos = event.position()
        for rect, item in self._hit_areas:
            if rect.contains(pos):
                tip = f"{item.title}\n重要度: {item.importance}  緊急度: {item.urgency}"
                QToolTip.showText(event.globalPosition().toPoint(), tip, self)
                return
        QToolTip.hideText()

    def paintEvent(self, event: object) -> None:  # noqa: ARG002
        """マトリクスを描画する."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        plot_w = w - _MARGIN * 2
        plot_h = h - _MARGIN * 2

        # 背景
        painter.fillRect(0, 0, w, h, QColor(COLORS["bg_primary"]))

        # 4象限の背景色
        half_w = plot_w / 2
        half_h = plot_h / 2

        q_colors = [
            (_MARGIN, _MARGIN, half_w, half_h, COLORS["q2_color"], 30),
            (_MARGIN + half_w, _MARGIN, half_w, half_h, COLORS["q1_color"], 30),
            (_MARGIN, _MARGIN + half_h, half_w, half_h, COLORS["q4_color"], 25),
            (
                _MARGIN + half_w,
                _MARGIN + half_h,
                half_w,
                half_h,
                COLORS["q3_color"],
                30,
            ),
        ]

        for qx, qy, qw, qh, color, alpha in q_colors:
            c = QColor(color)
            c.setAlpha(alpha)
            painter.fillRect(QRectF(qx, qy, qw, qh), c)

        # グリッド線
        pen = QPen(QColor(COLORS["border"]))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(1)
        painter.setPen(pen)

        painter.drawLine(
            int(_MARGIN + half_w), _MARGIN, int(_MARGIN + half_w), _MARGIN + plot_h
        )
        painter.drawLine(
            _MARGIN, int(_MARGIN + half_h), _MARGIN + plot_w, int(_MARGIN + half_h)
        )

        # 軸ラベル
        painter.setPen(QColor(COLORS["text_secondary"]))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)

        painter.drawText(
            QRectF(_MARGIN, h - _MARGIN + 10, plot_w, 30),
            Qt.AlignmentFlag.AlignCenter,
            "緊急度 →",
        )

        painter.save()
        painter.translate(_MARGIN - 35, _MARGIN + plot_h / 2)
        painter.rotate(-90)
        painter.drawText(
            QRectF(-plot_h / 2, 0, plot_h, 30),
            Qt.AlignmentFlag.AlignCenter,
            "重要度 →",
        )
        painter.restore()

        # 象限ラベル（領域名 + 説明ガイド）
        _pad = 8
        quadrant_guides = [
            (
                _MARGIN + _pad,
                _MARGIN + _pad,
                half_w - _pad * 2,
                half_h - _pad * 2,
                COLORS["q2_color"],
                "Q2: 効果性の領域",
                "最も注力すべき。緊急でないため後回しに"
                "しがちだが、長期的な成長につながる",
            ),
            (
                _MARGIN + half_w + _pad,
                _MARGIN + _pad,
                half_w - _pad * 2,
                half_h - _pad * 2,
                COLORS["q1_color"],
                "Q1: 必須の領域",
                "最優先で取り組む必要があるが、常にここに追われると燃え尽きの原因に",
            ),
            (
                _MARGIN + _pad,
                _MARGIN + half_h + _pad,
                half_w - _pad * 2,
                half_h - _pad * 2,
                COLORS["q4_color"],
                "Q4: 浪費/過剰の領域",
                "成果につながりにくい。リフレッシュならOKだが時間浪費に注意",
            ),
            (
                _MARGIN + half_w + _pad,
                _MARGIN + half_h + _pad,
                half_w - _pad * 2,
                half_h - _pad * 2,
                COLORS["q3_color"],
                "Q3: 錯覚の領域",
                "緊急だが自身の目標に関係ないことも多い。委任・断る選択も重要",
            ),
        ]

        for gx, gy, gw, gh, color, title, desc in quadrant_guides:
            # 領域名（9pt・象限色）
            font.setPointSize(9)
            painter.setFont(font)
            painter.setPen(QColor(color))
            title_rect = QRectF(gx, gy, gw, 20)
            painter.drawText(
                title_rect,
                int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop),
                title,
            )

            # 説明文（8pt・muted色・ワードラップ）
            font.setPointSize(8)
            painter.setFont(font)
            muted = QColor(COLORS["text_muted"])
            muted.setAlpha(180)
            painter.setPen(muted)
            desc_rect = QRectF(gx, gy + 20, gw, gh - 20)
            painter.drawText(
                desc_rect,
                int(
                    Qt.AlignmentFlag.AlignLeft
                    | Qt.AlignmentFlag.AlignTop
                    | Qt.TextFlag.TextWordWrap
                ),
                desc,
            )

        # アイテムのドット描画（オフセット済み座標を使用）
        self._calc_dot_positions(plot_w, plot_h)

        font.setPointSize(8)
        painter.setFont(font)
        fm = QFontMetrics(font)

        self._hit_areas = []

        for pos, item in self._dot_positions:
            dot_color = self._get_dot_color(item)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(dot_color))
            painter.drawEllipse(
                int(pos.x()) - _DOT_RADIUS,
                int(pos.y()) - _DOT_RADIUS,
                _DOT_RADIUS * 2,
                _DOT_RADIUS * 2,
            )

            # タイトル（長い場合は省略 + ツールチップで全文表示）
            title = item.title
            if len(title) > _LABEL_MAX_CHARS:
                title = title[: _LABEL_MAX_CHARS - 1] + "…"
            label_x = int(pos.x()) + 10
            label_y = int(pos.y()) + 4
            painter.setPen(QColor(COLORS["text_primary"]))
            painter.drawText(label_x, label_y, title)

            # ヒットエリア（ドット + ラベルを包含する矩形）
            label_w = fm.horizontalAdvance(title)
            label_h = fm.height()
            hit_rect = QRectF(
                pos.x() - _DOT_RADIUS,
                pos.y() - max(_DOT_RADIUS, label_h),
                _DOT_RADIUS + 10 + label_w + 4,
                max(_DOT_RADIUS * 2, label_h) + _DOT_RADIUS,
            )
            self._hit_areas.append((hit_rect, item))

        painter.end()
