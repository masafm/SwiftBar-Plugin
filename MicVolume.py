#!/usr/bin/env python3
# <bitbar.title>Mic Volume</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Masafumi Kashiwagi</bitbar.author>
# <bitbar.author.github>masafm</bitbar.author.github>
# <bitbar.desc>Mic Volume</bitbar.desc>
# <bitbar.dependencies>python3,applescript,switchaudio-osx</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/masafm/SwiftBar-Plugin/blob/main/MicVolume.sh</bitbar.abouturl>
# <swiftbar.type>streamable</swiftbar.type>

import signal
import sys
import subprocess
import time
import os
import shutil

INTERVAL=10
IGNORE_DEVICES=['ZoomAudioDevice','Microsoft Teams Audio']

def exit_program(sig, frame):
    sys.exit(0)

def refresh(sig, frame):
    show_mic_volume()

def get_current_device():
    cmd = ["SwitchAudioSource","-t","input","-c"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return p.stdout.strip()

def list_input_devices():
    cmd = ["SwitchAudioSource","-t","input","-a"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    devices=[]
    for d in p.stdout.strip().splitlines():
        if d not in IGNORE_DEVICES:
            devices.append(d)
    return devices

def change_input_device(dev):
    cmd = ["SwitchAudioSource","-t","input","-s",dev]
    p = subprocess.run(cmd, text=True)
    return p.returncode

def get_mic_volume():
    cmd = ["osascript","-e","return input volume of (get volume settings)"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return int(p.stdout.strip())
    
def change_mic_volume(volume):
    cmd = ["osascript","-e",f"set volume input volume {volume}"]
    p = subprocess.run(cmd, text=True)
    return p.returncode

def show_mic_volume():
    devices=list_input_devices()
    device=get_current_device()[0:1]
    if len([d for d in devices if d.startswith(device)]) > 1:
        device=get_current_device()[0:3]
    volume=(int)(get_mic_volume()/10)
    if volume == 10:
        volume = 'F'
    pid=os.getpid()
    print(f"""~~~
{device}:{volume} | size=16
---
Mic Volume
---
Minimize Mic Volume(F7) | bash='{sys.argv[0]}' param1=minimize_mic_volume param2={pid} terminal=false shortcut=F7
Maximize Mic Volume(F8) | bash='{sys.argv[0]}' param1=maximize_mic_volume param2={pid} terminal=false shortcut=F8
---""")
    for device in devices:
        print(f"{device} | bash='{sys.argv[0]}' param1=change_input_device param2={pid} param3='{device}' terminal=false")
    sys.stdout.flush()

os.environ["PATH"] = f"/opt/homebrew/bin:{os.environ.get('PATH')}"

if shutil.which("SwitchAudioSource") is None:
    print("Please install switchaudio-osx first", file=sys.stderr)
    print("https://github.com/deweller/switchaudio-osx", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) >= 3:
    pid = int(sys.argv[2])
    if sys.argv[1] == "minimize_mic_volume":
        change_mic_volume(0)
        time.sleep(0.5)
        os.kill(pid, signal.SIGUSR1)
        sys.exit(0)
    elif sys.argv[1] == "maximize_mic_volume":
        change_mic_volume(100)
        os.kill(pid, signal.SIGUSR1)
        time.sleep(0.5)
        sys.exit(0)
    elif sys.argv[1] == "change_input_device":
        change_input_device(sys.argv[3])
        os.kill(pid, signal.SIGUSR1)
        time.sleep(0.5)
        sys.exit(0)

signal.signal(signal.SIGTERM, exit_program)
signal.signal(signal.SIGUSR1, refresh)
signal.signal(signal.SIGALRM, refresh)
signal.setitimer(signal.ITIMER_REAL, 0.1, INTERVAL)

while True:
    time.sleep(3600)
