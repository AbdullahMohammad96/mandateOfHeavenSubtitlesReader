"""
NVDA App Module: Mandate Of Heaven Subtitle Reader

The game is Electron/browse mode. The treeInterceptor's full text looks like:

  line 0: (video player region label or empty)
  line 1: (subtitle text)  <-- this is what we want
  ...

We poll with core.callLater (NVDA main thread), read POSITION_ALL text,
split into lines, take line index 1 (second non-empty line), and speak
only when it changes.
"""

import appModuleHandler
import api
import speech
import ui
import core
import textInfos
import addonHandler
import logging
import sys
import os

_addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)

addonHandler.initTranslation()
log = logging.getLogger(__name__)

from shared import _get, _set

POLL_MS = 500


def _speak(text):
    if not text or not text.strip():
        return
    text = text.strip()
    if len(text) < _get("minLength"):
        return
    try:
        interrupt = _get("interruptSpeech")
        pri = speech.priorities.SpeechPriority.NOW if interrupt \
              else speech.priorities.SpeechPriority.NEXT
        speech.speakText(text, priority=pri)
    except Exception:
        try:
            ui.message(text)
        except Exception:
            pass


def _get_second_line(ti):
    """
    Read the full document text from the treeInterceptor,
    split into non-empty lines, and return line index 1 (the second line).
    Line 0 = video player label/region. Line 1 = subtitle text.
    Returns empty string if unavailable.
    """
    try:
        info = ti.makeTextInfo(textInfos.POSITION_ALL)
        text = info.text
        if not text:
            return ""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        log.debug(f"MANDATE: lines={lines[:5]}")
        if len(lines) >= 2:
            return lines[1]
        # If only one line, it might BE the subtitle (no video label present)
        if len(lines) == 1:
            return lines[0]
        return ""
    except Exception as e:
        log.debug(f"MANDATE: _get_second_line error: {e}")
        return ""


class AppModule(appModuleHandler.AppModule):

    def __init__(self, pid, appName=None):
        super().__init__(pid, appName)
        self._ti = None
        self._last_subtitle = ""
        self._polling = False
        log.info("MANDATE: AppModule loaded")
        core.callLater(1500, self._announce_startup)

    def _announce_startup(self):
        ui.message("Mandate Of Heaven subtitle reader active. NVDA+Shift+M to toggle.")
        if _get("enabled"):
            self._start_polling()

    def terminate(self):
        self._polling = False
        self._ti = None
        log.info("MANDATE: AppModule terminated")
        super().terminate()

    # ── treeInterceptor capture ────────────────────────────────────────────

    def _try_capture_ti(self, obj):
        try:
            ti = getattr(obj, 'treeInterceptor', None)
            if ti is not None and ti is not self._ti:
                self._ti = ti
                log.info(f"MANDATE: treeInterceptor captured: {ti}")
        except Exception:
            pass

    def event_treeInterceptor_gainFocus(self, obj, nextHandler):
        self._try_capture_ti(obj)
        nextHandler()

    def event_gainFocus(self, obj, nextHandler):
        self._try_capture_ti(obj)
        nextHandler()

    # ── polling ────────────────────────────────────────────────────────────

    def _start_polling(self):
        if self._polling:
            return
        self._polling = True
        self._last_subtitle = ""
        log.info("MANDATE: polling started")
        core.callLater(POLL_MS, self._tick)

    def _stop_polling(self):
        self._polling = False
        log.info("MANDATE: polling stopped")

    def _tick(self):
        if not self._polling:
            return
        try:
            self._do_tick()
        except Exception:
            log.exception("MANDATE: tick error")
        core.callLater(POLL_MS, self._tick)

    def _do_tick(self):
        if not _get("enabled"):
            return

        # Refresh treeInterceptor from current focus if we don't have one
        if self._ti is None:
            try:
                focus = api.getFocusObject()
                if focus and focus.appModule is self:
                    self._try_capture_ti(focus)
            except Exception:
                pass

        if self._ti is None:
            return

        text = _get_second_line(self._ti)
        if not text:
            return

        if text != self._last_subtitle:
            self._last_subtitle = text
            log.info(f"MANDATE: new subtitle: {repr(text[:80])}")
            _speak(text)

    # ── toggle ─────────────────────────────────────────────────────────────

    def script_toggle(self, gesture):
        enabled = not _get("enabled")
        _set("enabled", enabled)
        if enabled:
            self._start_polling()
            ui.message("Subtitle reader enabled.")
        else:
            self._stop_polling()
            ui.message("Subtitle reader disabled.")

    __gestures = {
        "kb:NVDA+shift+m": "toggle",
    }
