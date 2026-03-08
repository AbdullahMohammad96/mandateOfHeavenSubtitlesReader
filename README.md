# Mandate Of Heaven Subtitle Reader — NVDA Addon

An NVDA addon that automatically reads subtitles in the game **Mandate Of Heaven (江山北望)** as they appear, without requiring you to navigate with arrow keys.

---

## ⚠️ A Note From the Author

This addon was created mainly through AI assistance (Claude) by an inexperienced blind gamer who wanted to enjoy this game without struggling to keep up with fast-moving subtitles. The code works, but it is not the work of an experienced NVDA addon developer.

**If you are a developer and you find things that could be improved, your contributions are very welcome.** Please be kind with any criticisms — this was built out of necessity and a love of gaming, not professional expertise. Pull requests, suggestions, and bug reports are all appreciated.

---

## About the Game

[Mandate Of Heaven (江山北望)](https://store.steampowered.com/app/3831120/Mandate_Of_Heaven/) is a Chinese FMV/visual novel RPG built on Electron. NVDA reads it like a web page in browse mode, with subtitles rendered as centered text nodes inside an HTML5 video player region.

The game deliberately disables live region announcements on subtitle elements (`container-live:off`), which means NVDA will not automatically announce subtitle changes — and accessibility events like `nameChange` or `textChange` never fire for these nodes. This is why the addon uses polling rather than event hooks.

---

## How It Works

The addon uses `core.callLater` to poll on NVDA's own main thread every 200ms. On each tick it reads the full document text from the game's browse mode `treeInterceptor` via `makeTextInfo(POSITION_ALL)`, then splits the result into lines. The document structure is:

- **Line 1:** the video player region
- **Line 2:** the English subtitle text

The addon extracts line 2 and speaks it only when it has changed since the last tick. A rolling history of the last 10 spoken subtitles is kept so that fast-changing subtitles are not dropped, and so that a subtitle that briefly disappears and reappears is not spoken twice. No OCR or screen capture is used — everything is read directly from the accessibility tree.

---

## Installation

1. Download the latest `.nvda-addon` file from the [Releases](../../releases) page.
2. Double-click the file.
3. NVDA will ask if you want to install it — press Enter on **Yes**.
4. NVDA will then ask if you want to restart now — press Enter on **Yes** to apply the addon.

---

## Requirements

- **NVDA** 2022.1 or later (tested up to 2025.3.3)
- **Windows 10 or 11**
- **Mandate Of Heaven** installed via Steam

---

## Usage

Once installed, the addon activates automatically when the game launches. About 1.5 seconds after the game is detected, NVDA will announce that the subtitle reader is active. Subtitles will then be read aloud as they appear on screen.

### Keyboard Shortcut

| Shortcut | Action |
|---|---|
| `NVDA + Shift + M` | Toggle subtitle reading on or off |

---

## Settings

Go to **NVDA menu → Preferences → Settings → Mandate Of Heaven Subtitles**.

| Setting | Description |
|---|---|
| Enable automatic subtitle reading | Turn the addon on or off |
| Interrupt speech for new subtitles | If checked, new subtitles immediately interrupt whatever NVDA is currently saying |
| Minimum text length | Ignore any text shorter than this. Helps filter out stray UI elements. Default: 3 |

---

## Troubleshooting

**Subtitles are not being read:**
- Make sure the addon is enabled (NVDA should say "Mandate Of Heaven subtitle reader active" about 1.5 seconds after the game launches).
- Make sure NVDA is in browse mode inside the game (press `NVDA+Space` to toggle if needed).
- Check the NVDA log (NVDA menu → Tools → View Log) for lines starting with `MANDATE:`.

**Some subtitles are still being missed:**
- The addon polls every 200ms and tracks a history of recent subtitles to catch fast changes. If subtitles are still being missed, the game may be displaying them faster than the poll can catch. Please open an issue with details about which scene this happens in.

**The wrong text is being spoken:**
- The addon reads the second line of the document. If the game's page structure changes in a different version, the line numbering may be off. Please open an issue with details.

**Subtitles are being cut off because they change too fast:**
- Make sure **Interrupt speech** is enabled in settings so new subtitles immediately replace old ones.

---

## Technical Details

- **Game executable:** `project-beifa-client-full.exe`
- **Engine:** Electron (Chromium-based)
- **Subtitle element:** `IA2_ROLE_SECTION`, `text-align:center`, `container-live:off`
- **Reading method:** `core.callLater` polling at 200ms on NVDA's main thread, reading `treeInterceptor.makeTextInfo(POSITION_ALL)`, extracting the second non-empty line, speaking only on change
- **History tracking:** A rolling history of the last 10 spoken subtitles is kept to avoid re-speaking a subtitle that briefly disappears and reappears, while still catching fast-changing lines
- **Why polling and not events:** The game sets `container-live:off` on subtitle nodes, suppressing all accessibility change events. Polling is the only reliable approach.

---

## File Structure

```
mandateOfHeavenSubtitles/
├── manifest.ini              # Addon metadata
├── LICENSE                   # GPL-2 license
├── README.md                 # This file
├── appModules/
│   └── project-beifa-client-full.py   # Main app module
├── globalPlugins/
│   └── mandateSubtitleGlobal.py       # Registers settings panel globally
└── shared/
    └── __init__.py           # Config, settings panel, shared utilities
```

---

## Contributing

Contributions of any kind are welcome:
- Bug reports and feature requests via [Issues](../../issues)
- Code improvements via [Pull Requests](../../pulls)
- Testing on different systems and NVDA versions

Please be patient and kind — this project was made by someone learning as they go.

---

## License

This addon is licensed under the **GNU General Public License v2** — see [LICENSE](LICENSE) for details.

---

## Authors

- **Abdullah Mohammad** — blind gamer, idea and testing
- **Claude Code (Anthropic)** — AI-assisted development

---

## Acknowledgements

- The [NVDA](https://www.nvaccess.org/) project and NV Access for their incredible screen reader and open source codebase.
- Muyan Studio (木焱工作室) for making Mandate Of Heaven.
