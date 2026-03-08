"""
Shared config and settings panel for the Mandate Of Heaven subtitle reader addon.
"""

import config
import gui
from gui import guiHelper
import wx
import logging

log = logging.getLogger(__name__)

CONF_SECTION = "mandateOfHeavenSubtitles"
CONF_DEFAULTS = {
    "enabled": True,
    "interruptSpeech": True,
    "minLength": 3,
}

def _ensure_section():
    try:
        if CONF_SECTION not in config.conf:
            config.conf[CONF_SECTION] = {}
    except Exception:
        pass

def _get(key):
    try:
        _ensure_section()
        if key in config.conf[CONF_SECTION]:
            val = config.conf[CONF_SECTION][key]
            default = CONF_DEFAULTS[key]
            if isinstance(default, bool):
                return bool(val)
            if isinstance(default, int):
                return int(val)
            return val
        return CONF_DEFAULTS[key]
    except Exception:
        return CONF_DEFAULTS[key]

def _set(key, value):
    try:
        _ensure_section()
        config.conf[CONF_SECTION][key] = value
    except Exception:
        pass


class MandateSettingsPanel(gui.settingsDialogs.SettingsPanel):
    title = "Mandate Of Heaven Subtitles"

    def makeSettings(self, sizer):
        h = guiHelper.BoxSizerHelper(self, sizer=sizer)

        self.cbEnabled = h.addItem(wx.CheckBox(self, label="&Enable automatic subtitle reading"))
        self.cbEnabled.SetValue(_get("enabled"))

        self.cbInterrupt = h.addItem(wx.CheckBox(self, label="&Interrupt speech for new subtitles"))
        self.cbInterrupt.SetValue(_get("interruptSpeech"))

        self.spnMinLength = h.addLabeledControl(
            "&Minimum text length (ignore very short items):", wx.SpinCtrl,
            min=1, max=50, initial=_get("minLength"))

    def onSave(self):
        _set("enabled",         self.cbEnabled.GetValue())
        _set("interruptSpeech", self.cbInterrupt.GetValue())
        _set("minLength",       self.spnMinLength.GetValue())
