#!/usr/bin/env python3
# <bitbar.title>Zoom Mute State</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Masafumi Kashiwagi</bitbar.author>
# <bitbar.author.github>masafm</bitbar.author.github>
# <bitbar.desc>Zoom Mute State</bitbar.desc>
# <bitbar.dependencies>python3,applescript</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/masafm/SwiftBar-Plugin/blob/main/ZoomMuteState.py</bitbar.abouturl>
# <swiftbar.type>streamable</swiftbar.type>

import signal
import sys
import subprocess
import time
import os

INTERVAL=1
MUTE_STATE_SCRIPT='''property menuTitle : "ミーティング"
property btnDisableMute : "オーディオのミュート解除"
if application "zoom.us" is running then
    tell application "System Events"
        tell application process "zoom.us"
            if exists (menu bar item menuTitle of menu bar 1) then
                if exists (menu item btnDisableMute of menu 1 of menu bar item menuTitle of menu bar 1) then
                    return 1
                end if
            end if
        end tell
    end tell
end if
return'''
current_icon="unmute"

def exit_program(sig, frame):
    sys.exit(0)

def refresh(sig, frame):
    global current_icon
    if get_zoom_pid():
        if is_mute():
            show_mute_icon()
        else:
            show_unmute_icon()
    else:
        if current_icon == "unmute":
            show_mute_icon()

def is_mute():
    cmd = ["osascript"]
    p = subprocess.run(cmd, input=MUTE_STATE_SCRIPT, stdout=subprocess.PIPE, text=True)
    return p.stdout.strip().splitlines()

def show_mute_icon():
    global current_icon
    current_icon="mute"
    print("""~~~
:mic.slash.fill: | size=16
---
Zoom Mute State""")
    sys.stdout.flush()

def show_unmute_icon():
    global current_icon
    current_icon="unmute"
    print("""~~~
:mic.fill: | size=16
---
Zoom Mute State""")
    sys.stdout.flush()

def get_zoom_pid():
    cmd = ["pgrep","CptHost"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return p.stdout.strip().splitlines()

signal.signal(signal.SIGTERM, exit_program)
signal.signal(signal.SIGALRM, refresh)
signal.setitimer(signal.ITIMER_REAL, 0.1, INTERVAL)

while True:
    time.sleep(3600)
