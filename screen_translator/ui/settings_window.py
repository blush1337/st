from __future__ import annotations

from PySide6.QtCore import QEvent, QTimer, Qt, Signal
from PySide6.QtGui import QCloseEvent, QShowEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..config import (
    AppSettings,
    GeneralSettings,
    HotkeySettings,
    OCRSettings,
    OverlaySettings,
    TranslationSettings,
)
from ..hotkeys import hotkey_is_available
from .hotkey_edit import HotkeyEdit
from .motion import animate_page_in, animate_window_in, animate_window_out
from .theme import material_theme, settings_stylesheet


LANGUAGES = [
    ("Automatic", "auto"),
    ("Arabic", "ar"),
    ("Chinese (Simplified)", "zh-CN"),
    ("Chinese (Traditional)", "zh-TW"),
    ("English", "en"),
    ("French", "fr"),
    ("German", "de"),
    ("Italian", "it"),
    ("Japanese", "ja"),
    ("Korean", "ko"),
    ("Polish", "pl"),
    ("Portuguese", "pt"),
    ("Russian", "ru"),
    ("Spanish", "es"),
    ("Turkish", "tr"),
    ("Ukrainian", "uk"),
]


def _set_combo_data(combo: QComboBox, value: object) -> None:
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)


def _scroll_page(content: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QScrollArea.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setWidget(content)
    return area


class SettingsWindow(QDialog):
    saved = Signal(object)
    hiddenToTray = Signal()

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._settings = settings
        self._hiding_to_tray = False
        self._hide_origin = None
        self.setWindowTitle("Screen Region Translator settings")
        self.setObjectName("settingsWindow")
        self.setMinimumSize(720, 590)
        self.resize(760, 640)
        self.setStyleSheet(settings_stylesheet(material_theme()))

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 19, 22, 17)
        root.setSpacing(14)
        title = QLabel("Screen Region Translator")
        title.setObjectName("windowTitle")
        subtitle = QLabel("Capture a screen area, recognize its text, and show a translation.")
        subtitle.setObjectName("description")
        root.addWidget(title)
        root.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(16)
        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setFixedWidth(166)
        self.navigation.addItems(["General", "Translation", "Text recognition", "Overlay"])
        self.pages = QStackedWidget()
        body.addWidget(self.navigation)
        body.addWidget(self.pages, 1)
        root.addLayout(body, 1)

        self.pages.addWidget(_scroll_page(self._general_page()))
        self.pages.addWidget(_scroll_page(self._translation_page()))
        self.pages.addWidget(_scroll_page(self._ocr_page()))
        self.pages.addWidget(_scroll_page(self._overlay_page()))
        self.navigation.currentRowChanged.connect(self._switch_page)
        self.navigation.setCurrentRow(0)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_button is not None:
            save_button.setObjectName("primaryButton")
        root.addWidget(buttons)
        self.load(settings)

    @staticmethod
    def _page_layout(title: str, description: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        page.setObjectName("settingsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 2, 10, 12)
        layout.setSpacing(6)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        detail = QLabel(description)
        detail.setObjectName("description")
        detail.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(detail)
        return page, layout

    def _switch_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        current = self.pages.currentWidget()
        if current is not None:
            animate_page_in(current)

    def _general_page(self) -> QWidget:
        page, layout = self._page_layout(
            "General", "Control startup, tray behavior, and the capture shortcut."
        )
        behavior = QGroupBox("Application behavior")
        behavior_layout = QVBoxLayout(behavior)
        self.launch_startup = QCheckBox("Launch when I sign in to Windows")
        self.start_minimized = QCheckBox("Start minimized")
        self.minimize_tray = QCheckBox("Minimize to notification area")
        self.notifications = QCheckBox("Show notification-area messages")
        behavior_layout.addWidget(self.launch_startup)
        behavior_layout.addWidget(self.start_minimized)
        behavior_layout.addWidget(self.minimize_tray)
        behavior_layout.addWidget(self.notifications)
        layout.addWidget(behavior)

        hotkey_group = QGroupBox("Capture shortcut")
        hotkey_form = QFormLayout(hotkey_group)
        self.hotkey = HotkeyEdit()
        hotkey_row = QHBoxLayout()
        hotkey_row.addWidget(self.hotkey, 1)
        reset = QPushButton("Reset")
        reset.clicked.connect(lambda: self.hotkey.setShortcut("ctrl+shift+t"))
        hotkey_row.addWidget(reset)
        hotkey_form.addRow("Shortcut:", hotkey_row)
        note = QLabel("Click the field, then press one key together with Ctrl, Alt, Shift, or Win.")
        note.setObjectName("description")
        note.setWordWrap(True)
        hotkey_form.addRow("", note)
        layout.addWidget(hotkey_group)
        layout.addStretch()
        return page

    def _translation_page(self) -> QWidget:
        page, layout = self._page_layout(
            "Translation", "Choose the languages and service used for each capture."
        )
        languages = QGroupBox("Languages")
        form = QFormLayout(languages)
        self.source_language = QComboBox()
        self.target_language = QComboBox()
        for label, code in LANGUAGES:
            self.source_language.addItem(label, code)
            if code != "auto":
                self.target_language.addItem(label, code)
        form.addRow("Source:", self.source_language)
        form.addRow("Target:", self.target_language)
        layout.addWidget(languages)

        provider = QGroupBox("Provider")
        provider_form = QFormLayout(provider)
        self.provider = QComboBox()
        self.provider.addItem("Google Web (no API key)", "google_web")
        self.provider.addItem("LibreTranslate", "libretranslate")
        self.provider.addItem("No translation (testing)", "passthrough")
        self.libre_url = QLineEdit()
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("Optional on some servers")
        provider_form.addRow("Service:", self.provider)
        provider_form.addRow("Server URL:", self.libre_url)
        provider_form.addRow("API key:", self.api_key)
        note = QLabel(
            "Google Web is convenient for personal use but is not an official supported API. "
            "Use LibreTranslate when you need a service you control."
        )
        note.setObjectName("description")
        note.setWordWrap(True)
        provider_form.addRow("", note)
        self.provider.currentIndexChanged.connect(self._provider_changed)
        layout.addWidget(provider)
        layout.addStretch()
        return page

    def _ocr_page(self) -> QWidget:
        page, layout = self._page_layout(
            "Text recognition", "Tune recognition for screenshots of application and browser text."
        )
        engine = QGroupBox("Recognition engine")
        form = QFormLayout(engine)
        self.ocr_engine = QComboBox()
        self.ocr_engine.addItem("RapidOCR (local)", "rapidocr")
        self.ocr_language = QComboBox()
        self.ocr_language.addItem("English and Chinese", "en_zh")
        self.confidence = QDoubleSpinBox()
        self.confidence.setRange(0.1, 0.99)
        self.confidence.setSingleStep(0.05)
        self.confidence.setDecimals(2)
        self.preprocess = QCheckBox("Increase contrast before recognition")
        self.gpu = QCheckBox("Use GPU acceleration")
        self.gpu.setEnabled(False)
        self.gpu.setToolTip("The bundled ONNX setup uses the CPU provider")
        form.addRow("Engine:", self.ocr_engine)
        form.addRow("Model language:", self.ocr_language)
        form.addRow("Minimum confidence:", self.confidence)
        form.addRow("", self.preprocess)
        form.addRow("", self.gpu)
        note = QLabel("The OCR model loads on first capture and remains available for later captures.")
        note.setObjectName("description")
        note.setWordWrap(True)
        form.addRow("", note)
        layout.addWidget(engine)
        layout.addStretch()
        return page

    def _overlay_page(self) -> QWidget:
        page, layout = self._page_layout(
            "Overlay", "Set the appearance and lifetime of translated text."
        )
        appearance = QGroupBox("Appearance")
        form = QFormLayout(appearance)
        self.font_family = QFontComboBox()
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 32)
        self.auto_font = QCheckBox("Reduce font size for long translations")
        self.text_opacity = QSpinBox()
        self.text_opacity.setRange(30, 100)
        self.text_opacity.setSuffix("%")
        self.background_opacity = QSpinBox()
        self.background_opacity.setRange(50, 100)
        self.background_opacity.setSuffix("%")
        self.padding = QSpinBox()
        self.padding.setRange(6, 32)
        self.padding.setSuffix(" px")
        form.addRow("Font:", self.font_family)
        form.addRow("Font size:", self.font_size)
        form.addRow("", self.auto_font)
        form.addRow("Text opacity:", self.text_opacity)
        form.addRow("Background opacity:", self.background_opacity)
        form.addRow("Padding:", self.padding)
        layout.addWidget(appearance)

        behavior = QGroupBox("Behavior")
        behavior_form = QFormLayout(behavior)
        self.position = QComboBox()
        self.position.addItem("Automatic (near selection)", "automatic")
        self.position.addItem("Below selection", "below")
        self.position.addItem("Above selection", "above")
        self.show_original = QCheckBox("Show recognized text above the translation")
        behavior_form.addRow("Position:", self.position)
        behavior_form.addRow("", self.show_original)
        note = QLabel("The translation remains visible until you press Esc or choose Close.")
        note.setObjectName("description")
        note.setWordWrap(True)
        behavior_form.addRow("", note)
        layout.addWidget(behavior)
        layout.addStretch()
        return page

    def _provider_changed(self) -> None:
        enabled = self.provider.currentData() == "libretranslate"
        self.libre_url.setEnabled(enabled)
        self.api_key.setEnabled(enabled)

    def load(self, settings: AppSettings) -> None:
        self._settings = settings
        general = settings.general
        self.launch_startup.setChecked(general.launch_at_startup)
        self.start_minimized.setChecked(general.start_minimized)
        self.minimize_tray.setChecked(general.minimize_to_tray)
        self.notifications.setChecked(general.tray_notifications)
        self.hotkey.setShortcut(settings.hotkey.shortcut)

        translation = settings.translation
        _set_combo_data(self.source_language, translation.source_language)
        _set_combo_data(self.target_language, translation.target_language)
        _set_combo_data(self.provider, translation.provider)
        self.libre_url.setText(translation.libretranslate_url)
        self.api_key.setText(translation.api_key)
        self._provider_changed()

        ocr = settings.ocr
        _set_combo_data(self.ocr_engine, ocr.engine)
        _set_combo_data(self.ocr_language, ocr.language)
        self.confidence.setValue(ocr.confidence_threshold)
        self.preprocess.setChecked(ocr.preprocess)
        self.gpu.setChecked(ocr.gpu)

        overlay = settings.overlay
        self.font_family.setCurrentFont(overlay.font_family)
        self.font_size.setValue(overlay.font_size)
        self.auto_font.setChecked(overlay.automatic_font_size)
        self.text_opacity.setValue(overlay.text_opacity)
        self.background_opacity.setValue(overlay.background_opacity)
        self.padding.setValue(overlay.padding)
        _set_combo_data(self.position, overlay.position)
        self.show_original.setChecked(overlay.show_original)

    def collect(self) -> AppSettings:
        return AppSettings(
            general=GeneralSettings(
                launch_at_startup=self.launch_startup.isChecked(),
                start_minimized=self.start_minimized.isChecked(),
                minimize_to_tray=self.minimize_tray.isChecked(),
                tray_notifications=self.notifications.isChecked(),
                close_behavior="tray",
            ),
            hotkey=HotkeySettings(
                shortcut=self.hotkey.shortcut(), enabled=self._settings.hotkey.enabled
            ),
            translation=TranslationSettings(
                source_language=str(self.source_language.currentData()),
                target_language=str(self.target_language.currentData()),
                provider=str(self.provider.currentData()),
                libretranslate_url=self.libre_url.text().strip(),
                api_key=self.api_key.text(),
                timeout_seconds=self._settings.translation.timeout_seconds,
            ),
            ocr=OCRSettings(
                engine=str(self.ocr_engine.currentData()),
                language=str(self.ocr_language.currentData()),
                confidence_threshold=self.confidence.value(),
                preprocess=self.preprocess.isChecked(),
                gpu=self.gpu.isChecked(),
            ),
            overlay=OverlaySettings(
                font_family=self.font_family.currentFont().family(),
                font_size=self.font_size.value(),
                automatic_font_size=self.auto_font.isChecked(),
                text_opacity=self.text_opacity.value(),
                background_opacity=self.background_opacity.value(),
                padding=self.padding.value(),
                position=str(self.position.currentData()),
                show_original=self.show_original.isChecked(),
                auto_dismiss=False,
                dismiss_seconds=self._settings.overlay.dismiss_seconds,
            ),
        )

    def _save(self) -> None:
        if (
            self.hotkey.shortcut() != self._settings.hotkey.shortcut
            and not hotkey_is_available(self.hotkey.shortcut())
        ):
            QMessageBox.warning(
                self,
                "Shortcut unavailable",
                "Another application has reserved this shortcut. Choose a different combination.",
            )
            return
        self._settings = self.collect()
        self.saved.emit(self._settings)
        self.accept()

    def changeEvent(self, event: QEvent) -> None:
        if (
            event.type() == QEvent.Type.WindowStateChange
            and self.isMinimized()
            and self._settings.general.minimize_to_tray
        ):
            QTimer.singleShot(0, self._hide_to_tray)
        super().changeEvent(event)

    def reject(self) -> None:
        self._hide_to_tray()

    def _hide_to_tray(self) -> None:
        if not self.isVisible() or self._hiding_to_tray:
            return
        self.setWindowState(
            self.windowState() & ~Qt.WindowState.WindowMinimized
        )
        self._hiding_to_tray = True
        self._hide_origin = self.pos()
        animate_window_out(self, self._finish_hide_to_tray, offset_y=5)

    def _finish_hide_to_tray(self) -> None:
        self.hide()
        if self._hide_origin is not None:
            self.move(self._hide_origin)
        self.setWindowOpacity(1.0)
        self._hiding_to_tray = False
        self.hiddenToTray.emit()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, lambda: animate_window_in(self, offset_y=5))

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self._hide_to_tray()
