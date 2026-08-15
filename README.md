# Screen Region Translator

A Windows 10/11 notification-area utility that recognizes and translates text from a selected screen region. Press the global shortcut, drag over text, and copy the translated result from a compact overlay.

The current MVP includes:

- a configurable global shortcut (`Ctrl + Shift + T` by default);
- region selection on every connected monitor, including monitors with negative desktop coordinates;
- per-monitor DPI conversion and in-memory MSS capture;
- local RapidOCR recognition with confidence scores and four-point bounding boxes;
- Google Web, LibreTranslate, and no-translation test providers behind one interface;
- selectable translated text, copy/close controls, `Esc`, outside-click dismissal, and automatic placement;
- startup, tray, OCR, translation, and overlay settings stored per Windows user;
- a pausable notification-area icon and clean worker-thread shutdown;
- rotating diagnostic logs with no API-key logging.

## Run from source

Python 3.11 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python main.py
```

The OCR model initializes on the first capture, so that capture takes longer than later ones. Recognition and translation run outside the Qt GUI thread.

Settings are stored at:

```text
%LOCALAPPDATA%\Screen Region Translator\settings.json
```

Logs are stored beside the settings in `screen-translator.log`. LibreTranslate credentials are never included in logs. The API key is stored in the per-user settings file, so protect that Windows account and file as you would any locally stored application credential.

### Diagnostic mode

Normal logging records every major stage and its duration. For physical capture coordinates, OCR filtering counts, full diagnostic tracebacks, and console output, start the application from PowerShell with:

```powershell
python main.py --debug
```

Entries use a searchable form such as:

```text
stage=capture event=started operation_id="8c31e62a" logical_width=420 logical_height=180
stage=capture event=completed operation_id="8c31e62a" duration_ms=18.7
stage=ocr event=results_ready operation_id="8c31e62a" accepted_items=3
stage=translation event=completed operation_id="8c31e62a" duration_ms=241.3
```

The same `operation_id` connects capture, OCR, and translation records for one selection. Logs contain dimensions, providers, language codes, counts, timings, and error types. They deliberately omit captured pixels, recognized text, translated text, and API-key values.

## Everyday use

1. Open **Settings → Translation** and choose the target language.
2. Minimize or close Settings; the utility remains in the notification area.
3. Press `Ctrl + Shift + T` in any application.
4. Drag over text on one monitor and release.
5. Select or copy the translated text. Press `Esc` or click elsewhere to dismiss it.

Tiny selections are ignored. Press `Esc` before releasing the mouse to cancel. The tray menu also provides **Translate Region**, **Settings**, **Pause Hotkey**, and **Exit**.

## Translation providers

**Google Web** is the default because it works without setup, but it is an unofficial personal-use endpoint and does not provide a service-level guarantee. **LibreTranslate** accepts a server URL and optional API key and is the appropriate choice for a controlled deployment. **No translation** keeps the recognized text unchanged and is useful when testing OCR.

Providers implement this contract:

```python
class Translator:
    def translate(
        self,
        text: str,
        source_language: str | None,
        target_language: str,
    ) -> str: ...
```

## Monitor and scaling behavior

Selection uses one transparent Qt window per monitor. A selection is expressed in that monitor's logical coordinates and converted using its device pixel ratio before MSS capture. This handles secondary monitors, negative origins, and different scale factors without assuming that the primary monitor begins at `(0, 0)`.

The MVP intentionally constrains one drag to one monitor. You can translate from any monitor, but a single rectangle cannot span two monitors. This avoids ambiguous physical coordinates when adjacent displays use different scale factors.

## Tests

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
```

The automated suite covers settings migration and persistence, shortcut parsing, negative-coordinate overlay placement, structured OCR output, pipeline behavior, provider failures, and a settings-window round trip. The screen capture and global-shortcut behaviors still require a real interactive Windows session.

Before releasing a build, manually verify:

- capture while another application has focus;
- cancellation with `Esc` and rejection of tiny selections;
- primary and secondary monitors, including negative origins and mixed scaling;
- normal Windows UI text and browser text;
- network, invalid-key, and no-text errors;
- settings persistence, shortcut changes, pause/resume, and tray exit.

## Package without a console window

Install PyInstaller only in the build environment, then collect the OCR models:

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name ScreenRegionTranslator --collect-all rapidocr_onnxruntime main.py
```

The generated application is placed under `dist\ScreenRegionTranslator`. Build outputs, virtual environments, model caches, credentials, and logs are excluded by `.gitignore`.

## Code layout

```text
screen_translator/
├── app.py                 application lifecycle and worker orchestration
├── capture.py             per-monitor physical capture
├── config.py              typed settings and atomic JSON persistence
├── hotkeys.py             shortcut parsing, conflict check, and listener
├── models.py              OCR and pipeline result data
├── ocr.py                 reusable RapidOCR engine
├── pipeline.py            capture → OCR → translation
├── translation/           provider interface and implementations
└── ui/                    selector, settings, tray, and result overlay
```

