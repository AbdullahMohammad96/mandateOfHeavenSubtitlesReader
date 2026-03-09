# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.3] - 2026-03-09

### Changed
- The polling loop now checks for a Video Player node (role=151, name="Video Player") at the start of every tick. If no video is playing, the tick returns immediately without walking the tree — keeping NVDA fast and responsive in menus, chapter selection, and dialogue screens.
- No changes to how subtitles are read — role=7 STATICTEXT detection is unchanged.

### Fixed
- NVDA no longer slows down when navigating the game UI outside of video scenes.

---

## [1.2] - 2026-03-09

### Changed
- Completely rewrote subtitle detection. Instead of reading the full document via `makeTextInfo(POSITION_ALL)` and guessing by line position, the addon now walks the accessibility tree looking specifically for **STATICTEXT nodes (role=7)** whose text does not contain CJK (Chinese/Japanese/Korean) characters.
- This reads node names directly from IAccessible2, bypassing NVDA's virtual buffer cache entirely — so subtitles are available immediately without waiting for the buffer to finish building.

### Fixed
- Subtitles no longer missed at the start of new scenes.
- "Unable to play media" no longer repeats — the video element's fallback text is filtered out.
- Tabbing through buttons no longer interferes with subtitle reading.
- "Mandate of Heaven" window title no longer repeats — only leaf STATICTEXT nodes are read, never container names.

---

## [1.1] - 2026-03-08

### Added
- NVDA+Shift+A diagnostic shortcut: dumps the full accessibility tree to `mandate_tree_dump.txt` on the Desktop. This was the key diagnostic that revealed subtitles live in role=7 STATICTEXT nodes, leading to the v1.2 rewrite.
- Pre-parsing of all English VTT subtitle files from the game's `.pack` files (ASAR format) at startup, stored in memory for reference.

### Changed
- Poll interval reduced to 50ms.
- Addon now searches all treeInterceptors seen for the app process, not just the most recently focused one.

---

## [1.0] - 2026-03-08

### Added
- Initial release.
- App module for `project-beifa-client-full.exe` (Mandate Of Heaven / 江山北望).
- 500ms polling loop using `core.callLater` on NVDA's main thread.
- Reads subtitle text via `treeInterceptor.makeTextInfo(POSITION_ALL)`, extracts the second non-empty line.
- Suppresses consecutive duplicate subtitles.
- NVDA+Shift+M toggle shortcut.
- Settings panel under NVDA menu → Preferences → Settings → Mandate Of Heaven Subtitles, with options for enable/disable, speech interrupt mode, and minimum text length.
- Startup announcement spoken 1.5 seconds after game is detected.
