"""
NVDA App Module: Mandate Of Heaven Subtitle Reader

Page structure:
- Line 1: video player
- Line 2: English subtitles (the only thing we care about)

We hook event_treeInterceptor_gainFocus to get the document,
then use event_liveRegionChange, event_nameChange and event_textChange
on the second line's object. Since container-live is off, we also
watch the treeInterceptor's caret/text change events.

Actually: we use a virtualBuffer textInfo to find the second line object,
then watch it for changes via NVDA's object event system.
"""

import appModuleHandler
import api
import speech
import ui
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


def _get_second_line_text(ti):
    """
    Read the second line from the treeInterceptor document.
    Line 1 = video player, Line 2 = subtitle text.
    Returns the text of line 2, or empty string.
    """
    try:
        info = ti.makeTextInfo(textInfos.POSITION_FIRST)
        # Move to end of line 1
        info.expand(textInfos.UNIT_LINE)
        info.collapse(end=True)
        # Now expand to get line 2
        info.expand(textInfos.UNIT_LINE)
        text = info.text.strip()
        return text
    except Exception as e:
        log.debug(f"MANDATE: _get_second_line_text error: {e}")
        return ""


class AppModule(appModuleHandler.AppModule):

    def __init__(self, pid, appName=None):
        super().__init__(pid, appName)
        self._ti = None
        self._last_subtitle = ""
        appModuleHandler._mandateMonitor = self
        log.info("MANDATE: AppModule loaded")
        ui.message("Mandate Of Heaven subtitle reader active. NVDA+Shift+M to toggle.")

    def terminate(self):
        self._ti = None
        appModuleHandler._mandateMonitor = None
        log.info("MANDATE: AppModule terminated")
        super().terminate()

    def event_treeInterceptor_gainFocus(self, obj, nextHandler):
        try:
            ti = obj.treeInterceptor
            if ti is not None:
                self._ti = ti
                log.info("MANDATE: treeInterceptor ready")
        except Exception:
            pass
        nextHandler()

    def event_gainFocus(self, obj, nextHandler):
        try:
            ti = getattr(obj, 'treeInterceptor', None)
            if ti is not None and ti is not self._ti:
                self._ti = ti
                log.info("MANDATE: treeInterceptor captured via gainFocus")
        except Exception:
            pass
        nextHandler()

    def event_liveRegionChange(self, obj, nextHandler):
        if _get("enabled") and self._ti is not None:
            self._check_subtitle()
        nextHandler()

    def event_nameChange(self, obj, nextHandler):
        if _get("enabled") and self._ti is not None:
            self._check_subtitle()
        nextHandler()

    def event_valueChange(self, obj, nextHandler):
        if _get("enabled") and self._ti is not None:
            self._check_subtitle()
        nextHandler()

    def event_textChange(self, obj, nextHandler):
        if _get("enabled") and self._ti is not None:
            self._check_subtitle()
        nextHandler()

    def event_reorder(self, obj, nextHandler):
        """Fires when child nodes are added/removed — common for subtitle updates."""
        if _get("enabled") and self._ti is not None:
            self._check_subtitle()
        nextHandler()

    def event_show(self, obj, nextHandler):
        """Fires when a new element becomes visible."""
        if _get("enabled") and self._ti is not None:
            self._check_subtitle()
        nextHandler()

    def _check_subtitle(self):
        try:
            text = _get_second_line_text(self._ti)
            if text and text != self._last_subtitle:
                self._last_subtitle = text
                log.info(f"MANDATE: new subtitle: {repr(text[:80])}")
                _speak(text)
        except Exception:
            log.exception("MANDATE: _check_subtitle error")

    def script_toggle(self, gesture):
        enabled = not _get("enabled")
        _set("enabled", enabled)
        ui.message("Subtitle reader enabled." if enabled else "Subtitle reader disabled.")

    __gestures = {
        "kb:NVDA+shift+m": "toggle",
    }
