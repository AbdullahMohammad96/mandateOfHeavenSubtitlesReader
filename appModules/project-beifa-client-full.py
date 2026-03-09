"""
NVDA App Module: Mandate Of Heaven Subtitle Reader v1.3

Complete rewrite. Instead of polling the DOM for subtitle text,
we read the VTT subtitle files directly from the game's pack files
and play them back using precise timers.

How it works:
1. At startup, pre-parse all English VTT cues from all chapter pack files.
   Each cue is stored as (start_ms, end_ms, text) keyed by vtt filename.

2. We poll the DOM lightly (200ms) only to detect WHICH video is playing,
   by looking for a <track> or <video> src attribute that names a VTT file.

3. When a new VTT filename is detected, we record the start time and
   schedule each cue using core.callLater with the exact VTT timestamp.
   The first subtitle fires at e.g. 3080ms — never missed.

4. If we can't detect the VTT name from the DOM, we fall back to watching
   file access times on the pack files to guess which scene just started.
"""

import appModuleHandler
import api
import speech
import ui
import core
import controlTypes
import treeInterceptorHandler
import addonHandler
import logging
import sys
import os
import struct
import json
import time
import re

_addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)

addonHandler.initTranslation()
log = logging.getLogger(__name__)

from shared import _get, _set

# How often to poll DOM for video source change (ms)
DETECT_POLL_MS = 50

GAME_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\江山北望"
LANGUAGE = "en"  # Only English for now; could be made configurable


def _parse_vtt_time(t):
    """Parse VTT timestamp string to milliseconds."""
    t = t.strip()
    parts = t.replace(',', '.').split(':')
    try:
        if len(parts) == 2:
            return int(float(parts[0]) * 60000 + float(parts[1]) * 1000)
        elif len(parts) == 3:
            return int(float(parts[0]) * 3600000 + float(parts[1]) * 60000 + float(parts[2]) * 1000)
    except Exception:
        pass
    return 0


def _parse_vtt(content):
    """Parse VTT content into list of (start_ms, end_ms, text) tuples."""
    cues = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if '-->' in line:
            parts = line.split('-->')
            start = _parse_vtt_time(parts[0])
            end = _parse_vtt_time(parts[1].split()[0])
            text_lines = []
            i += 1
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1
            text = ' '.join(text_lines)
            if text:
                cues.append((start, end, text))
        i += 1
    return cues


def _load_pack(path):
    """Parse an ASAR pack file, return dict of filename -> VTT cues."""
    result = {}
    try:
        with open(path, 'rb') as f:
            raw = f.read()
        size2 = struct.unpack('<I', raw[12:16])[0]
        header_size = struct.unpack('<I', raw[8:12])[0]
        toc = json.loads(raw[16:16 + size2])
        data_start = 16 + header_size

        def walk(node, path):
            if 'files' in node:
                for name, child in node['files'].items():
                    walk(child, path + '/' + name)
            else:
                offset = int(node['offset'])
                size = node['size']
                content = raw[data_start + offset:data_start + offset + size].decode('utf-8', errors='replace')
                filename = os.path.basename(path)
                cues = _parse_vtt(content)
                if cues:
                    result[filename] = cues

        walk(toc, '')
    except Exception as e:
        log.warning(f"MANDATE: failed to load pack {path}: {e}")
    return result


def _load_all_cues(game_dir, language):
    """Load all VTT cues from all chapter pack files for the given language."""
    all_cues = {}
    suffix = f"_{language}.pack"
    try:
        for fname in os.listdir(game_dir):
            if fname.endswith(suffix):
                path = os.path.join(game_dir, fname)
                cues = _load_pack(path)
                all_cues.update(cues)
                log.info(f"MANDATE: loaded {len(cues)} VTTs from {fname}")
    except Exception as e:
        log.error(f"MANDATE: _load_all_cues error: {e}")
    log.info(f"MANDATE: total VTT files loaded: {len(all_cues)}")
    return all_cues


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


def _get_playing_vtt(focus):
    """
    Try to find the currently playing VTT filename from the DOM.
    Looks for <track> src or <video> src attributes in the accessibility tree.
    Returns a VTT filename (e.g. '00_001_001.vtt') or None.
    """
    try:
        ti = treeInterceptorHandler.getTreeInterceptor(focus)
        if ti is None:
            ti = getattr(focus, 'treeInterceptor', None)
        if ti is None:
            return None
        root = ti.rootNVDAObject
        if root is None:
            return None

        # Walk nodes looking for one with a .vtt URL in name/value/description
        queue = [root]
        seen = set()
        count = 0
        vtt_pattern = re.compile(r'([\w\-]+\.vtt)', re.IGNORECASE)
        while queue and count < 500:
            node = queue.pop(0)
            nid = id(node)
            if nid in seen:
                continue
            seen.add(nid)
            count += 1
            for attr in ('name', 'value', 'description', 'URL'):
                try:
                    val = getattr(node, attr, None)
                    if val and isinstance(val, str):
                        m = vtt_pattern.search(val)
                        if m:
                            return m.group(1)
                except Exception:
                    pass
            try:
                child = node.firstChild
                while child is not None:
                    queue.append(child)
                    try:
                        child = child.next
                    except Exception:
                        break
            except Exception:
                pass
    except Exception as e:
        log.debug(f"MANDATE: _get_playing_vtt error: {e}")
    return None



def _has_cjk(text):
    """Return True if text contains Chinese/Japanese/Korean characters."""
    return any('一' <= c <= '鿿' or
               '぀' <= c <= 'ヿ' or
               '가' <= c <= '힯'
               for c in text)


def _get_subtitle_text(focus):
    """
    Find subtitle text by looking for STATICTEXT (role=7) nodes in the
    accessibility tree that contain non-CJK text and are short enough
    to be a subtitle (not UI labels).
    Returns the subtitle string, or empty string if none found.
    """
    try:
        ti = treeInterceptorHandler.getTreeInterceptor(focus)
        if ti is None:
            ti = getattr(focus, 'treeInterceptor', None)
        root = ti.rootNVDAObject if ti else focus
    except Exception:
        root = focus

    candidates = []
    try:
        queue = [root]
        seen = set()
        count = 0
        while queue and count < 500:
            node = queue.pop(0)
            nid = id(node)
            if nid in seen:
                continue
            seen.add(nid)
            count += 1

            try:
                role = node.role
                # Role 7 = STATICTEXT — the only role subtitles appear as
                if int(role) == 7:
                    name = getattr(node, 'name', None)
                    if name and isinstance(name, str):
                        name = name.strip()
                        if name and not _has_cjk(name):
                            words = len(name.split())
                            if words <= 30:
                                candidates.append(name)
            except Exception:
                pass

            try:
                child = node.firstChild
                while child is not None:
                    queue.append(child)
                    try:
                        child = child.next
                    except Exception:
                        break
            except Exception:
                pass
    except Exception as e:
        log.debug(f"MANDATE: _get_subtitle_text error: {e}")

    log.debug(f"MANDATE: candidates={candidates}")
    if not candidates:
        return ""
    # Return the longest candidate (subtitle text is usually longer than labels)
    return max(candidates, key=len)


def _has_video_player(focus):
    """
    Return True if the accessibility tree contains a Video Player node
    (role=151, name='Video Player'). Tells us a video is actively loaded.
    """
    try:
        ti = treeInterceptorHandler.getTreeInterceptor(focus)
        if ti is None:
            ti = getattr(focus, 'treeInterceptor', None)
        root = ti.rootNVDAObject if ti else focus
    except Exception:
        root = focus
    try:
        queue = [root]
        seen = set()
        count = 0
        while queue and count < 500:
            node = queue.pop(0)
            nid = id(node)
            if nid in seen:
                continue
            seen.add(nid)
            count += 1
            try:
                if int(node.role) == 151:
                    name = getattr(node, 'name', None)
                    if name and 'Video Player' in name:
                        return True
            except Exception:
                pass
            try:
                child = node.firstChild
                while child is not None:
                    queue.append(child)
                    try:
                        child = child.next
                    except Exception:
                        break
            except Exception:
                pass
    except Exception:
        pass
    return False


class AppModule(appModuleHandler.AppModule):

    def __init__(self, pid, appName=None):
        super().__init__(pid, appName)
        self._cues = {}
        self._current_vtt = None
        self._play_start = 0
        self._cue_gen = 0
        self._polling = False
        self._loaded = False
        self._last_spoken = ""
        self._last_seen = ""
        log.info("MANDATE: AppModule loading v1.3")
        core.callLater(100, self._load_cues_async)
        core.callLater(1500, self._announce_startup)

    def _load_cues_async(self):
        """Load all VTT cues in a deferred call so we don't block NVDA startup."""
        self._cues = _load_all_cues(GAME_DIR, LANGUAGE)
        self._loaded = True
        log.info(f"MANDATE: cues ready, {len(self._cues)} VTT files")

    def _announce_startup(self):
        ui.message("Mandate Of Heaven subtitle reader active. NVDA+Shift+M to toggle.")
        if _get("enabled"):
            self._start_polling()

    def terminate(self):
        self._polling = False
        self._cue_gen += 1  # cancel all pending cues
        log.info("MANDATE: AppModule terminated")
        super().terminate()


    def _start_polling(self):
        if self._polling:
            return
        self._polling = True
        self._current_vtt = None
        log.info("MANDATE: polling started")
        core.callLater(DETECT_POLL_MS, self._tick)

    def _stop_polling(self):
        self._polling = False
        self._cue_gen += 1
        log.info("MANDATE: polling stopped")

    def _tick(self):
        if not self._polling:
            return
        try:
            self._do_tick()
        except Exception:
            log.exception("MANDATE: tick error")
        core.callLater(DETECT_POLL_MS, self._tick)

    def _do_tick(self):
        if not _get("enabled"):
            return

        try:
            focus = api.getFocusObject()
            if not focus or focus.appModule is not self:
                return
        except Exception:
            return

        # Quick check — if no Video Player node present, we're not on a video screen
        if not _has_video_player(focus):
            if self._last_spoken:
                self._last_spoken = ""
                self._last_seen = ""
            return

        text = _get_subtitle_text(focus)
        if not text:
            self._last_seen = ""
            return

        if text == self._last_spoken and text == self._last_seen:
            return

        self._last_seen = text
        self._last_spoken = text
        log.info(f"MANDATE: subtitle: {repr(text[:80])}")
        _speak(text)

    def _start_vtt(self, vtt_filename):
        """Start playing cues for the given VTT file."""
        cues = self._cues.get(vtt_filename)
        if not cues:
            log.info(f"MANDATE: no cues for {vtt_filename}")
            return

        log.info(f"MANDATE: starting VTT {vtt_filename} with {len(cues)} cues")
        self._current_vtt = vtt_filename
        self._play_start = time.monotonic()
        self._cue_gen += 1
        gen = self._cue_gen

        for start_ms, end_ms, text in cues:
            # Schedule each cue at its exact timestamp
            delay = max(0, start_ms)
            _text = text
            _gen = gen
            def make_speaker(t, g):
                def speak_cue():
                    if not self._polling or not _get("enabled"):
                        return
                    if self._cue_gen != g:
                        return  # cancelled — new VTT started
                    log.info(f"MANDATE: cue: {repr(t[:60])}")
                    _speak(t)
                return speak_cue
            core.callLater(delay, make_speaker(_text, _gen))

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

