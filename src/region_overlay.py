"""Интерактивное выделение прямоугольной области экрана мышью —
полноэкранный полупрозрачный оверлей поверх уже сделанного снимка,
как в Flameshot/Spectacle. Реализовано на чистом Qt, поэтому одинаково
работает на X11 (Linux) и на Windows.

На Wayland этот модуль не используется: там для выделения применяется
внешняя утилита `slurp` (см. capture.py), т.к. клиентское приложение не
может просто нарисовать поверх экрана произвольный снимок — это отдаёт
композитору сам протокол Wayland.
"""
from PyQt5.QtCore import QEventLoop, QPoint, QRect, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QGuiApplication, QPainter, QPen
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget

SELECTION_COLOR = QColor(58, 110, 165)       # #3a6ea5 — фирменный цвет иконки
DIM_COLOR = QColor(0, 0, 0, 130)
MIN_SELECTION_SIZE = 6                        # px — меньше считаем случайным кликом


class _RegionOverlay(QWidget):
    """Полноэкранное окно: рисует затемнённый снимок экрана, позволяет
    выделить прямоугольник мышью, затем показывает мини-панель с
    выбором действия (сохранить / скопировать / отмена)."""

    finished = pyqtSignal(str)  # 'save' | 'copy' | 'cancel'

    def __init__(self, background_pixmap, geometry):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.background = background_pixmap
        self.setGeometry(geometry)
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self.origin = QPoint()
        self.rect_selected = QRect()
        self.selecting = False
        self.locked = False
        self.toolbar = None

    # -- отрисовка -------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.background)
        painter.fillRect(self.rect(), DIM_COLOR)

        if not self.rect_selected.isNull():
            # "проявляем" исходный снимок внутри выделенной области
            painter.drawPixmap(self.rect_selected, self.background, self.rect_selected)
            pen = QPen(SELECTION_COLOR, 2)
            painter.setPen(pen)
            painter.drawRect(self.rect_selected.adjusted(0, 0, -1, -1))

            label = f"{self.rect_selected.width()} × {self.rect_selected.height()}"
            painter.setPen(QColor(255, 255, 255))
            label_y = (
                self.rect_selected.top() - 8
                if self.rect_selected.top() > 24
                else self.rect_selected.bottom() + 18
            )
            painter.drawText(self.rect_selected.left(), max(label_y, 12), label)
        elif not self.selecting:
            painter.setPen(QColor(255, 255, 255))
            hint_rect = self.rect().adjusted(0, 24, 0, 0)
            painter.drawText(hint_rect, Qt.AlignHCenter | Qt.AlignTop,
                              "Выделите область мышью — Esc для отмены")

    # -- мышь --------------------------------------------------------
    def mousePressEvent(self, event):
        if self.locked or event.button() != Qt.LeftButton:
            return
        self.origin = event.pos()
        self.selecting = True
        self.rect_selected = QRect(self.origin, self.origin)
        self.update()

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.rect_selected = QRect(self.origin, event.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if not self.selecting or event.button() != Qt.LeftButton:
            return
        self.selecting = False
        self.rect_selected = QRect(self.origin, event.pos()).normalized()

        if (self.rect_selected.width() < MIN_SELECTION_SIZE
                or self.rect_selected.height() < MIN_SELECTION_SIZE):
            # слишком маленькая область — считаем случайным кликом,
            # даём попробовать выделить ещё раз, не закрывая оверлей
            self.rect_selected = QRect()
            self.update()
            return

        self.locked = True
        self.update()
        self._show_toolbar()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._finish("cancel")
        else:
            super().keyPressEvent(event)

    # -- панель действий ---------------------------------------------
    def _show_toolbar(self):
        self.toolbar = QWidget(self)
        self.toolbar.setStyleSheet("background-color: #2c2c2c; border-radius: 6px;")
        layout = QHBoxLayout(self.toolbar)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        button_style = (
            "QPushButton { color: white; background-color: #3a6ea5;"
            " border: none; border-radius: 4px; padding: 6px 12px; }"
            "QPushButton:hover { background-color: #4a7eb5; }"
        )

        save_btn = QPushButton("Сохранить")
        save_btn.setStyleSheet(button_style)
        save_btn.clicked.connect(lambda: self._finish("save"))

        copy_btn = QPushButton("Копировать")
        copy_btn.setStyleSheet(button_style)
        copy_btn.clicked.connect(lambda: self._finish("copy"))

        cancel_btn = QPushButton("✕")
        cancel_btn.setFixedWidth(32)
        cancel_btn.setStyleSheet(button_style)
        cancel_btn.clicked.connect(lambda: self._finish("cancel"))

        for btn in (save_btn, copy_btn, cancel_btn):
            layout.addWidget(btn)

        self.toolbar.adjustSize()

        x = self.rect_selected.left()
        y = self.rect_selected.bottom() + 8
        if y + self.toolbar.height() > self.height():
            y = self.rect_selected.top() - self.toolbar.height() - 8
        x = max(4, min(x, self.width() - self.toolbar.width() - 4))
        y = max(4, y)

        self.toolbar.move(x, y)
        self.toolbar.show()
        save_btn.setFocus()

    def _finish(self, action):
        self.finished.emit(action)
        self.close()


def select_region_interactive():
    """Показывает интерактивный оверлей выделения поверх первичного
    экрана и блокирует выполнение (через вложенный QEventLoop, не
    останавливая остальной event loop приложения) до тех пор, пока
    пользователь не завершит выделение или не отменит его.

    Возвращает (action, rect, background):
      action     — 'save' | 'copy' | 'cancel'
      rect       — QRect выделенной области в координатах background
                   (None при отмене)
      background — QPixmap всего экрана, использованный как фон оверлея
                   (нужен вызывающей стороне, чтобы вырезать регион)

    Примечание: захват ограничен первичным экраном (как и обычный
    полноэкранный снимок в этом приложении) — мультимониторные
    конфигурации могут поддерживаться в будущем.
    """
    screen = QGuiApplication.primaryScreen()
    geometry = screen.geometry()
    background = screen.grabWindow(0)

    overlay = _RegionOverlay(background, geometry)
    result = {"action": "cancel"}

    def on_finished(action):
        result["action"] = action

    overlay.finished.connect(on_finished)

    loop = QEventLoop()
    overlay.finished.connect(loop.quit)

    overlay.showFullScreen()
    overlay.activateWindow()
    overlay.setFocus()

    loop.exec_()

    rect = overlay.rect_selected if result["action"] != "cancel" else None
    return result["action"], rect, background
