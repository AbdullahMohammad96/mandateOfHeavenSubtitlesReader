# Mandate Of Heaven Subtitle Reader — NVDA Addon

An NVDA addon that automatically reads subtitles in the game **Mandate Of Heaven (江山北望)** as they appear, without requiring you to navigate with arrow keys.

---

## ⚠️ A Note From the Author

This addon was created mainly through AI assistance (Claude) by an inexperienced blind gamer who wanted to enjoy this game without struggling to keep up with fast-moving subtitles. The code works, but it is not the work of an experienced NVDA addon developer.

**If you are a developer and you find things that could be improved, your contributions are very welcome.** Please be kind with any criticisms — this was built out of necessity and a love of gaming, not professional expertise. Pull requests, suggestions, and bug reports are all appreciated.

---

## About the Game

[Mandate Of Heaven (江山北望)](https://store.steampowered.com/app/3831120/Mandate_Of_Heaven/) is a Chinese FMV/visual novel RPG built on Electron. NVDA reads it like a web page, with subtitles rendered as centered text nodes inside an HTML5 video player region. The game deliberately disables aria-live on subtitle elements (`container-live:off`), which means NVDA does not automatically announce subtitle changes — hence the need for this addon.

---

## How It Works

The addon hooks into NVDA's `event_treeInterceptor_gainFocus` event, which fires when the game's browse mode document becomes ready. It then polls the accessibility tree via `treeInterceptor.makeTextInfo(POSITION_ALL)` to read all visible text, and speaks any lines that are new since the last poll.

No OCR or screen capture is used — the addon reads directly from the accessibility tree, the same way NVDA does when you press the arrow keys manually.

---

## Installation

1. Download the latest `.nvda-addon` file from the [Releases](../../releases) page.
2. Double-click the file.
3. NVDA will ask if you want to install it — press Enter on **Yes**.
4. NVDA will say that add-ons have changed and it will ask to restart, press **yes**.

---

## Requirements

- **NVDA** 2022.1 or later (tested up to 2025.3.3)
- **Windows 10 or 11**
- **Mandate Of Heaven** installed via Steam

---

## Usage

Once installed, the addon activates automatically when the game launches. Subtitles will be read aloud by NVDA as they appear on screen.

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
| Poll interval (ms) | How often the addon checks for new subtitles. Lower = more responsive but more CPU. Default: 500ms |
| Minimum text length | Ignore any text shorter than this. Helps filter out stray UI elements. Default: 3 |

---

## Troubleshooting

**Subtitles are not being read:**
- Make sure the addon is enabled (NVDA should say "Mandate Of Heaven subtitle reader active" when the game launches).
- Make sure NVDA is in browse mode inside the game (press `NVDA+Space` to toggle if needed).
- Check the NVDA log (NVDA menu → Tools → View Log) for lines starting with `MANDATE:`.

**Too much text is being spoken (UI elements, menus, etc.):**
- Increase the **Minimum text length** in settings to filter out short items.
- Try increasing the poll interval slightly.

**Subtitles are being cut off because they change too fast:**
- Reduce the **Poll interval** in settings to e.g. 200ms.
- Make sure **Interrupt speech** is enabled so new subtitles don't queue behind old ones.

---

## Technical Details

- **Game executable:** `project-beifa-client-full.exe`
- **Engine:** Electron (Chromium-based)
- **Subtitle element:** `IA2_ROLE_SECTION`, `text-align:center`, `container-live:off`
- **Reading method:** `treeInterceptor.makeTextInfo(POSITION_ALL)` polled on a background thread after `event_treeInterceptor_gainFocus`

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
- The developers of [subtitle_reader](https://github.com/maxe-hsieh/subtitle_reader) whose addon provided useful reference.
- Muyan Studio (木焱工作室) for making Mandate Of Heaven.
