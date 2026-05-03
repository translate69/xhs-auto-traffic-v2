# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, ".")
from core.browser_manager import BrowserManager
import config

bm = BrowserManager()
print("HEADLESS:", config.HEADLESS)
print("COOKIE_FILE:", config.COOKIE_FILE)
print("COOKIE_FILE exists:", config.COOKIE_FILE.exists())
