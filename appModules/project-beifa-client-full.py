"""
NVDA App Module: Mandate Of Heaven Subtitle Reader

The game is Electron with an HTML5 <video> + <track> for subtitles.
Subtitles render into a centered IA2_ROLE_SECTION div below the video.
aria-live is off so no events fire — must poll.

Critical fix: don't start polling in __init__ (treeInterceptor not ready yet).
Instead hook event_treeInterceptor_gainFocus which fires once the browse mode
document is loaded and ready. Then poll via a background thread using
a treeInterceptor reference captured at that point.
"""

import appModuleHandler
import api
import speech
import ui
import textInfos
import addonHandler
import logging
import threading
import time
import sys
import os

_addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)

addonHandler.initTranslation()
log = logging.getLogger(__name__)

from shared import _get, _set


class AppModule(appModuleHandler.AppModule):

    def __init__(self, pid, appName=None):
        super().__init__(pid, appName)
        self._known = set()
        self._running = False
        self._thread = None
        self._ti = None  # treeInterceptor reference, set when ready
        appModuleHandler._mandateMonitor = self
        log.info("MANDATE: AppModule loaded")
        ui.message("Mandate Of Heaven subtitle reader loaded. NVDA+Shift+M to toggle.")

    def terminate(self):
        self._running = False
        appModuleHandler._mandateMonitor = None
        log.info("MANDATE: AppModule terminated")
        super().terminate()

    def event_treeInterceptor_gainFocus(self, obj, nextHandler):
        """
        Fires when the browse mode document becomes active.
        This is the correct time to start polling — treeInterceptor is ready.
        """
        log.info(f"MANDATE: treeInterceptor_gainFocus, obj={obj}, ti={getattr(obj, 'treeInterceptor', None)}")
        try:
            ti = obj.treeInterceptor
            if ti is not None and ti is not self._ti:
                self._ti = ti
                log.info(f"MANDATE: got treeInterceptor {ti}, starting poll")
                if _get("enabled") and not self._running:
                    self._start_polling()
        except Exception:
            log.exception("MANDATE: error in treeInterceptor_gainFocus")
        nextHandler()

    def event_gainFocus(self, obj, nextHandler):
        """Also try to grab treeInterceptor on regular focus events."""
        try:
            ti = getattr(obj, 'treeInterceptor', None)
            if ti is not None and ti is not self._ti:
                self._ti = ti
                log.info(f"MANDATE: got treeInterceptor via gainFocus: {ti}")
                if _get("enabled") and not self._running:
                    self._start_polling()
        except Exception:
            pass
        nextHandler()

    def _start_polling(self):
        if self._running:
            return
        self._running = True
        self._known = set()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        log.info("MANDATE: polling thread started")

    def _stop_polling(self):
        self._running = False
        log.info("MANDATE: polling thread stopped")

    def _poll_loop(self):
        while self._running:
            try:
                if _get("enabled") and self._ti is not None:
                    self._tick()
            except Exception:
                log.exception("MANDATE: poll loop error")
            time.sleep(_get("pollInterval") / 1000.0)

    def _tick(self):
        try:
            info = self._ti.makeTextInfo(textInfos.POSITION_ALL)
            text = info.text
        except Exception as e:
            log.debug(f"MANDATE: makeTextInfo failed: {e}")
            return

        if not text:
            return

        min_len = _get("minLength")
        lines = [l.strip() for l in text.splitlines()
                 if l.strip() and len(l.strip()) >= min_len]

        if not lines:
            return

        log.debug(f"MANDATE: got {len(lines)} lines, first={repr(lines[0][:80])}")

        current = set(lines)
        new_lines = current - self._known
        self._known = current

        if not new_lines:
            return

        ordered = []
        seen = set()
        for l in lines:
            if l in new_lines and l not in seen:
                seen.add(l)
                ordered.append(l)

        text_to_speak = " ".join(ordered)
        log.info(f"MANDATE: speaking: {repr(text_to_speak[:100])}")

        try:
            interrupt = _get("interruptSpeech")
            pri = speech.priorities.SpeechPriority.NOW if interrupt \
                  else speech.priorities.SpeechPriority.NEXT
            speech.speakText(text_to_speak, priority=pri)
        except Exception:
            try:
                ui.message(text_to_speak)
            except Exception:
                pass

    def script_toggle(self, gesture):
        enabled = not _get("enabled")
        _set("enabled", enabled)
        if enabled:
            if self._ti is not None:
                self._start_polling()
            ui.message("Subtitle reader enabled.")
        else:
            self._stop_polling()
            ui.message("Subtitle reader disabled.")

    __gestures = {
        "kb:NVDA+shift+m": "toggle",
    }
