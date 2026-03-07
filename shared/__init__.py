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
    "pollInterval": 500,
}

def _get(key):
    try:
        val = config.conf[CONF_SECTION].get(key, CONF_DEFAULTS[key])
        default = CONF_DEFAULTS[key]
        if isinstance(default, bool):
            return bool(val)
        if isinstance(default, int):
            return int(val)
        return val
    except Exception:
        return CONF_DEFAULTS[key]

def _set(key, value):
    try:
        if CONF_SECTION not in config.conf:
            config.conf[CONF_SECTION] = {}
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

        self.spnInterval = h.addLabeledControl(
            "Poll interval (&ms):", wx.SpinCtrl,
            min=100, max=5000, initial=_get("pollInterval"))

        self.spnMinLength = h.addLabeledControl(
            "&Minimum text length (ignore very short items):", wx.SpinCtrl,
            min=1, max=50, initial=_get("minLength"))

    def onSave(self):
        _set("enabled",         self.cbEnabled.GetValue())
        _set("interruptSpeech", self.cbInterrupt.GetValue())
        _set("pollInterval",    self.spnInterval.GetValue())
        _set("minLength",       self.spnMinLength.GetValue())
        import appModuleHandler
        mon = getattr(appModuleHandler, "_mandateMonitor", None)
        if mon:
            mon.stop()
            if _get("enabled"):
                mon.start()
