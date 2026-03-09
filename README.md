# Mandate Of Heaven Subtitle Reader — NVDA Addon

An NVDA addon that automatically reads subtitles in the game **Mandate Of Heaven (江山北望)** as they appear, without requiring you to navigate with arrow keys.

---

## ⚠️ A Note From the Author

This addon was created mainly through AI assistance (Claude) by an inexperienced blind gamer who wanted to enjoy this game without struggling to keep up with fast-moving subtitles. The code works, but it is not the work of an experienced NVDA addon developer.

**If you are a developer and you find things that could be improved, your contributions are very welcome.** Please be kind with any criticisms — this was built out of necessity and a love of gaming, not professional expertise. Pull requests, suggestions, and bug reports are all appreciated.

---

## About the Game

[Mandate Of Heaven (江山北望)](https://store.steampowered.com/app/3831120/Mandate_Of_Heaven/) is a live-action FMV interactive film-game developed by the independent Chinese studio 木焱工作室 (Muyan Studio), released on Steam in November 2025.

You play as the Second Prince of the Xuan Kingdom — a southern regime clinging to half its realm after northern invaders have seized the capital and taken the royal family captive. The Tianhe river divides a fractured world: to the south, indulgence and uneasy peace; to the north, bones and unending war. As prince, you must decide whether to launch a Northern Campaign to reclaim the lost homeland, navigate the treacherous politics of a complacent imperial court, forge alliances, uncover betrayals, and ultimately write your own chapter of this grand imperial epic. Every choice you make plays out in real-time through cinematic live-action footage — the story branches dramatically depending on your decisions, with multiple endings.

The game is built on Electron (Chromium) and NVDA reads it in browse mode. Subtitles are rendered as static text nodes inside an HTML5 video player region in the accessibility tree.

---

## How It Works

The addon uses `core.callLater` to poll on NVDA's main thread every 50ms. Each tick works as follows:

1. **Video player check:** The accessibility tree is scanned for a node with role=151 and name "Video Player". If none is found, the tick returns immediately — zero overhead when you are in menus or dialogue screens.
2. **Subtitle search:** If a video is playing, the tree is walked looking for **STATICTEXT nodes (role=7)** whose text does not contain CJK (Chinese/Japanese/Korean) characters. These are the subtitle text nodes.
3. **Speak on change:** The longest matching candidate is taken as the current subtitle. It is spoken only when it differs from the last spoken text. A blank gap between cues resets the state so the same subtitle can be re-spoken if it appears again.

No OCR, screen capture, or virtual buffer text extraction is used — everything is read directly from IAccessible2 node names, which are always live regardless of whether NVDA's virtual buffer has finished loading.

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
- **Subtitle node:** role=7 (STATICTEXT), English text, short length
- **Video player node:** role=151, name="Video Player"
- **Reading method:** `core.callLater` polling at 50ms, walking IAccessible2 node tree directly, reading `.name` from leaf STATICTEXT nodes, speaking only on change
- **CJK filter:** Nodes containing Chinese/Japanese/Korean characters are skipped — these are UI labels, not subtitles
- **Idle behaviour:** If no Video Player node is present in the tree, each tick returns immediately without a full tree walk
- **Why polling and not events:** The game sets `container-live:off` on subtitle nodes, suppressing all accessibility change events. Polling is the only reliable approach.
- **Why not virtual buffer:** NVDA's virtual buffer cache is stale during scene transitions. Reading `.name` directly from IAccessible2 nodes bypasses the cache and is always current.

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
