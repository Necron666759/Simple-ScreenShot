"""Простое окно настроек: папка сохранения, три горячие клавиши
(сохранение в файл, копирование в буфер обмена, выделение области —
все независимые), автозапуск, формат файла и качество снимков."""
import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QCheckBox, QComboBox, QKeySequenceEdit,
    QMessageBox, QGroupBox, QRadioButton, QButtonGroup,
)
from PyQt5.QtGui import QKeySequence

import config as cfgmod
import autostart as autostart_mod
from hotkey import parse_hotkey, HotkeyError
from capture import is_wayland

# (ключ конфига, подпись поля, значение по умолчанию)
HOTKEY_FIELDS = (
    ("hotkey", "Сохранить снимок в файл:", "Print"),
    ("clipboard_hotkey", "Скопировать в буфер обмена:", "Ctrl+Print"),
    ("region_hotkey", "Выделить область экрана:", "Shift+Print"),
)


class SettingsDialog(QDialog):
    def __init__(self, cfg, on_apply, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки — Simple Screenshot")
        self.cfg = dict(cfg)
        self.on_apply = on_apply
        self.hotkey_edits = {}  # cfg_key -> QKeySequenceEdit
        self._build_ui()
        self.setMinimumWidth(460)

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 1) Место сохранения
        path_box = QGroupBox("Место сохранения скриншотов")
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(self.cfg.get("save_dir", ""))
        browse_btn = QPushButton("Обзор…")
        browse_btn.clicked.connect(self._choose_dir)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        path_box.setLayout(path_layout)
        layout.addWidget(path_box)

        # 2) Горячие клавиши — сохранение, буфер обмена, выделение области
        hotkey_box = QGroupBox("Горячие клавиши")
        hotkey_form = QFormLayout()

        for cfg_key, label, default in HOTKEY_FIELDS:
            edit = QKeySequenceEdit()
            try:
                edit.setKeySequence(QKeySequence(self.cfg.get(cfg_key, default)))
            except Exception:
                pass
            hotkey_form.addRow(label, edit)
            self.hotkey_edits[cfg_key] = edit

        hotkey_box_layout = QVBoxLayout()
        hotkey_box_layout.addLayout(hotkey_form)

        if is_wayland():
            note_text = (
                "Обнаружена сессия Wayland: приложения не могут перехватывать "
                "глобальные клавиши напрямую. Назначьте эти комбинации в "
                "настройках вашего окружения (раздел «Клавиши/Сочетания клавиш») "
                "на команды: simple-screenshot --capture (сохранить в файл), "
                "simple-screenshot --copy (скопировать в буфер обмена) и "
                "simple-screenshot --region (выделить область)."
            )
        else:
            note_text = (
                "Все комбинации перехватываются глобально в любой момент "
                "работы сессии, независимо от того, какое окно активно."
            )
        note = QLabel(note_text)
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 11px;")
        hotkey_box_layout.addWidget(note)
        hotkey_box.setLayout(hotkey_box_layout)
        layout.addWidget(hotkey_box)

        # 3) Автозапуск
        self.autostart_check = QCheckBox(
            "Запускать автоматически при входе в систему (фоново, в трее)"
        )
        self.autostart_check.setChecked(self.cfg.get("autostart", False))
        layout.addWidget(self.autostart_check)

        # 4) Формат
        fmt_box = QGroupBox("Формат файла")
        fmt_layout = QHBoxLayout()
        self.fmt_group = QButtonGroup(self)
        self.rb_png = QRadioButton("PNG")
        self.rb_jpg = QRadioButton("JPG")
        self.fmt_group.addButton(self.rb_png)
        self.fmt_group.addButton(self.rb_jpg)
        if self.cfg.get("format", "png") == "jpg":
            self.rb_jpg.setChecked(True)
        else:
            self.rb_png.setChecked(True)
        fmt_layout.addWidget(self.rb_png)
        fmt_layout.addWidget(self.rb_jpg)
        fmt_box.setLayout(fmt_layout)
        layout.addWidget(fmt_box)

        # 5) Качество
        quality_box = QGroupBox("Качество снимков")
        quality_layout = QHBoxLayout()
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Низкое", "low")
        self.quality_combo.addItem("Среднее", "medium")
        self.quality_combo.addItem("Высокое", "high")
        idx = self.quality_combo.findData(self.cfg.get("quality", "high"))
        self.quality_combo.setCurrentIndex(idx if idx >= 0 else 2)
        quality_layout.addWidget(self.quality_combo)
        quality_box.setLayout(quality_layout)
        layout.addWidget(quality_box)

        # Кнопки
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _choose_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранения", self.path_edit.text()
        )
        if d:
            self.path_edit.setText(d)

    def _save(self):
        save_dir = self.path_edit.text().strip()
        if not save_dir:
            QMessageBox.warning(self, "Ошибка", "Укажите папку для сохранения.")
            return
        save_dir = os.path.expanduser(save_dir)
        try:
            os.makedirs(save_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать папку: {e}")
            return

        # Считываем все горячие клавиши и проверяем, что каждая задана
        hotkey_texts = {}
        for cfg_key, label, _default in HOTKEY_FIELDS:
            text = self.hotkey_edits[cfg_key].keySequence().toString()
            if not text:
                QMessageBox.warning(self, "Ошибка", f"Задайте комбинацию клавиш: {label}")
                return
            hotkey_texts[cfg_key] = text

        # Проверяем, что все три комбинации попарно различны
        seen = {}
        for cfg_key, label, _default in HOTKEY_FIELDS:
            norm = hotkey_texts[cfg_key].strip().lower()
            if norm in seen:
                other_label = seen[norm]
                QMessageBox.warning(
                    self, "Ошибка",
                    f"Горячие клавиши «{other_label}» и «{label}» совпадают. "
                    "Назначьте каждому действию свою комбинацию.",
                )
                return
            seen[norm] = label

        if not is_wayland():
            for cfg_key, label, _default in HOTKEY_FIELDS:
                try:
                    parse_hotkey(hotkey_texts[cfg_key])
                except HotkeyError as e:
                    QMessageBox.warning(
                        self, "Некорректная комбинация", f"«{label}»: {e}",
                    )
                    return

        self.cfg["save_dir"] = save_dir
        for cfg_key, _label, _default in HOTKEY_FIELDS:
            self.cfg[cfg_key] = hotkey_texts[cfg_key]
        self.cfg["autostart"] = self.autostart_check.isChecked()
        self.cfg["format"] = "jpg" if self.rb_jpg.isChecked() else "png"
        self.cfg["quality"] = self.quality_combo.currentData()

        cfgmod.save_config(self.cfg)
        autostart_mod.set_autostart(self.cfg["autostart"])

        if self.on_apply:
            self.on_apply(self.cfg)

        self.accept()
