"""Простое окно настроек: папка сохранения, три горячие клавиши
(сохранение в файл, копирование в буфер обмена, выделение области —
все независимые), автозапуск, формат файла и качество снимков.

Рядом с кнопкой "Обзор"/"Browse" — переключатель языка интерфейса
EN/RU: переключается мгновенно (без нажатия "Сохранить") и сразу же
применяется ко всему открытому диалогу и к меню трея."""
import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QCheckBox, QComboBox, QKeySequenceEdit,
    QMessageBox, QGroupBox, QRadioButton, QButtonGroup,
)
from PyQt5.QtGui import QKeySequence

import config as cfgmod
import autostart as autostart_mod
import i18n
from i18n import tr
from hotkey import parse_hotkey, HotkeyError
from capture import is_wayland

# (ключ конфига, ключ перевода подписи поля, значение по умолчанию)
HOTKEY_FIELDS = (
    ("hotkey", "settings.hotkey.save", "Print"),
    ("clipboard_hotkey", "settings.hotkey.clipboard", "Ctrl+Print"),
    ("region_hotkey", "settings.hotkey.region", "Shift+Print"),
)

# (значение конфига, ключ перевода подписи) — для комбобокса качества
QUALITY_LEVELS = (
    ("low", "settings.quality.low"),
    ("medium", "settings.quality.medium"),
    ("high", "settings.quality.high"),
)


class SettingsDialog(QDialog):
    def __init__(self, cfg, on_apply, parent=None, on_language_change=None):
        super().__init__(parent)
        self.cfg = dict(cfg)
        self.on_apply = on_apply
        # Колбэк, которым TrayApp просит обновить меню трея сразу же
        # при переключении языка (не дожидаясь "Сохранить").
        self.on_language_change = on_language_change
        self.hotkey_edits = {}      # cfg_key -> QKeySequenceEdit
        self.hotkey_labels = {}     # cfg_key -> QLabel (подпись строки формы)
        self._build_ui()
        self.setMinimumWidth(460)
        self._retranslate()

    # -- построение UI ----------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 1) Место сохранения — переключатель языка EN/RU стоит в этой же
        # строке, сразу после кнопки "Обзор"/"Browse".
        self.path_box = QGroupBox()
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(self.cfg.get("save_dir", ""))
        self.browse_btn = QPushButton()
        self.browse_btn.clicked.connect(self._choose_dir)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)

        path_layout.addSpacing(10)
        self.lang_group = QButtonGroup(self)
        self.lang_group.setExclusive(True)
        self.btn_lang_en = QPushButton("EN")
        self.btn_lang_ru = QPushButton("RU")
        for btn in (self.btn_lang_en, self.btn_lang_ru):
            btn.setCheckable(True)
            btn.setFixedWidth(40)
        self.lang_group.addButton(self.btn_lang_en)
        self.lang_group.addButton(self.btn_lang_ru)
        self.btn_lang_en.clicked.connect(lambda: self._switch_language("en"))
        self.btn_lang_ru.clicked.connect(lambda: self._switch_language("ru"))
        path_layout.addWidget(self.btn_lang_en)
        path_layout.addWidget(self.btn_lang_ru)

        self.path_box.setLayout(path_layout)
        layout.addWidget(self.path_box)

        # 2) Горячие клавиши — сохранение, буфер обмена, выделение области
        self.hotkey_box = QGroupBox()
        hotkey_form = QFormLayout()

        for cfg_key, label_key, default in HOTKEY_FIELDS:
            edit = QKeySequenceEdit()
            try:
                edit.setKeySequence(QKeySequence(self.cfg.get(cfg_key, default)))
            except Exception:
                pass
            label = QLabel()
            hotkey_form.addRow(label, edit)
            self.hotkey_edits[cfg_key] = edit
            self.hotkey_labels[cfg_key] = label

        hotkey_box_layout = QVBoxLayout()
        hotkey_box_layout.addLayout(hotkey_form)

        self.hotkey_note = QLabel()
        self.hotkey_note.setWordWrap(True)
        self.hotkey_note.setStyleSheet("color: gray; font-size: 11px;")
        hotkey_box_layout.addWidget(self.hotkey_note)
        self.hotkey_box.setLayout(hotkey_box_layout)
        layout.addWidget(self.hotkey_box)

        # 3) Автозапуск
        self.autostart_check = QCheckBox()
        self.autostart_check.setChecked(self.cfg.get("autostart", False))
        layout.addWidget(self.autostart_check)

        # 4) Формат
        self.fmt_box = QGroupBox()
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
        self.fmt_box.setLayout(fmt_layout)
        layout.addWidget(self.fmt_box)

        # 5) Качество
        self.quality_box = QGroupBox()
        quality_layout = QHBoxLayout()
        self.quality_combo = QComboBox()
        for value, _label_key in QUALITY_LEVELS:
            self.quality_combo.addItem("", value)
        idx = self.quality_combo.findData(self.cfg.get("quality", "high"))
        self.quality_combo.setCurrentIndex(idx if idx >= 0 else 2)
        quality_layout.addWidget(self.quality_combo)
        self.quality_box.setLayout(quality_layout)
        layout.addWidget(self.quality_box)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton()
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._save)
        self.cancel_btn = QPushButton()
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    # -- язык интерфейса ---------------------------------------------------
    def _switch_language(self, lang):
        if lang == i18n.get_language():
            self._sync_lang_buttons()
            return
        i18n.set_language(lang)
        self.cfg["language"] = lang
        self._retranslate()
        if self.on_language_change:
            self.on_language_change()

    def _sync_lang_buttons(self):
        current = i18n.get_language()
        self.btn_lang_en.setChecked(current == "en")
        self.btn_lang_ru.setChecked(current == "ru")

    def _retranslate(self):
        """Обновляет текст всех виджетов диалога на текущий язык, не
        трогая уже введённые пользователем значения (путь, хоткеи и т.д.)."""
        self._sync_lang_buttons()
        self.setWindowTitle(tr("settings.title"))

        self.path_box.setTitle(tr("settings.save_location"))
        self.browse_btn.setText(tr("settings.browse"))

        self.hotkey_box.setTitle(tr("settings.hotkeys"))
        for cfg_key, label_key, _default in HOTKEY_FIELDS:
            self.hotkey_labels[cfg_key].setText(tr(label_key))
        self.hotkey_note.setText(
            tr("settings.hotkey_note_wayland") if is_wayland()
            else tr("settings.hotkey_note_default")
        )

        self.autostart_check.setText(tr("settings.autostart"))

        self.fmt_box.setTitle(tr("settings.format"))
        self.quality_box.setTitle(tr("settings.quality"))
        for i, (_value, label_key) in enumerate(QUALITY_LEVELS):
            self.quality_combo.setItemText(i, tr(label_key))

        self.save_btn.setText(tr("settings.save"))
        self.cancel_btn.setText(tr("settings.cancel"))

    # -- обработчики ---------------------------------------------------
    def _choose_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, tr("settings.choose_dir_title"), self.path_edit.text()
        )
        if d:
            self.path_edit.setText(d)

    def _save(self):
        save_dir = self.path_edit.text().strip()
        if not save_dir:
            QMessageBox.warning(self, tr("settings.error.title"), tr("settings.error.no_dir"))
            return
        save_dir = os.path.expanduser(save_dir)
        try:
            os.makedirs(save_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, tr("settings.error.title"), tr("settings.error.mkdir_failed", error=e))
            return

        # Считываем все горячие клавиши и проверяем, что каждая задана
        hotkey_texts = {}
        for cfg_key, label_key, _default in HOTKEY_FIELDS:
            text = self.hotkey_edits[cfg_key].keySequence().toString()
            if not text:
                QMessageBox.warning(
                    self, tr("settings.error.title"),
                    tr("settings.error.hotkey_missing", label=tr(label_key)),
                )
                return
            hotkey_texts[cfg_key] = text

        # Проверяем, что все три комбинации попарно различны
        seen = {}
        for cfg_key, label_key, _default in HOTKEY_FIELDS:
            norm = hotkey_texts[cfg_key].strip().lower()
            if norm in seen:
                other_label = seen[norm]
                QMessageBox.warning(
                    self, tr("settings.error.title"),
                    tr("settings.error.hotkey_duplicate", first=other_label, second=tr(label_key)),
                )
                return
            seen[norm] = tr(label_key)

        if not is_wayland():
            for cfg_key, label_key, _default in HOTKEY_FIELDS:
                try:
                    parse_hotkey(hotkey_texts[cfg_key])
                except HotkeyError as e:
                    QMessageBox.warning(
                        self, tr("settings.error.hotkey_invalid_title"),
                        f"«{tr(label_key)}»: {e}",
                    )
                    return

        self.cfg["save_dir"] = save_dir
        for cfg_key, _label_key, _default in HOTKEY_FIELDS:
            self.cfg[cfg_key] = hotkey_texts[cfg_key]
        self.cfg["autostart"] = self.autostart_check.isChecked()
        self.cfg["format"] = "jpg" if self.rb_jpg.isChecked() else "png"
        self.cfg["quality"] = self.quality_combo.currentData()
        self.cfg["language"] = i18n.get_language()

        cfgmod.save_config(self.cfg)
        autostart_mod.set_autostart(self.cfg["autostart"])

        if self.on_apply:
            self.on_apply(self.cfg)

        self.accept()
