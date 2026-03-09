"""
Global Plugin: Mandate Of Heaven Subtitle Reader
Registers the settings panel in NVDA's Settings dialog.
"""

import globalPluginHandler
import gui
import sys
import os

_addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)

from shared import MandateSettingsPanel


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    def __init__(self):
        super().__init__()
        if MandateSettingsPanel not in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
            gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(MandateSettingsPanel)

    def terminate(self):
        try:
            gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(MandateSettingsPanel)
        except ValueError:
            pass
        super().terminate()
