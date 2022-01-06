#!/usr/bin/env python3
# <bitbar.title>Mic Volume</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Masafumi Kashiwagi</bitbar.author>
# <bitbar.author.github>masafm</bitbar.author.github>
# <bitbar.desc>Mic Volume</bitbar.desc>
# <bitbar.dependencies>python3,applescript,https://github.com/deweller/switchaudio-osx</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/masafm/SwiftBar-Plugin/blob/main/MicVolume.sh</bitbar.abouturl>
# <swiftbar.type>streamable</swiftbar.type>

import signal
import sys
import subprocess
import time
import os
INTERVAL=10

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
    return p.stdout.strip().splitlines()

def change_input_device(dev):
    cmd = ["SwitchAudioSource","-t","input","-s",dev]
    p = subprocess.run(cmd, text=True)
    return p.returncode

def get_mic_volume():
    cmd = ["osascript","-e","return input volume of (get volume settings)"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return p.stdout.strip()
    
def change_mic_volume(volume):
    cmd = ["osascript","-e",f"set volume input volume {volume}"]
    p = subprocess.run(cmd, text=True)
    return p.returncode

def show_mic_volume():
    device=get_current_device()[0:6]
    volume=get_mic_volume()
    pid=os.getpid()
    print(f"""~~~
{device}({volume}) | size=16
---
Mic Volume
---
マイク音量最小化(F7) | bash='{sys.argv[0]}' param1=minimize_mic_volume param2={pid} terminal=false shortcut=F7
マイク音量最大化(F8) | bash='{sys.argv[0]}' param1=maximize_mic_volume param2={pid} terminal=false shortcut=F8
---""")
    for device in list_input_devices():
        if device != "ZoomAudioDevice" and device != "IOUSBHostInterface":
            print(f"{device} | bash='{sys.argv[0]}' param1=change_input_device param2={pid} param3='{device}' terminal=false")
    sys.stdout.flush()
        
signal.signal(signal.SIGTERM, exit_program)
signal.signal(signal.SIGUSR1, refresh)

if len(sys.argv) >= 3:
    pid = int(sys.argv[2])
    if sys.argv[1] == "minimize_mic_volume":
        change_mic_volume(0)
        os.kill(pid, signal.SIGUSR1)
        sys.exit(0)
    elif sys.argv[1] == "maximize_mic_volume":
        change_mic_volume(100)
        os.kill(pid, signal.SIGUSR1)
        sys.exit(0)
    elif sys.argv[1] == "change_input_device":
        change_input_device(sys.argv[3])
        os.kill(pid, signal.SIGUSR1)
        sys.exit(0)

i=INTERVAL
while True:
    if i == INTERVAL:
        show_mic_volume()
        i=1
    time.sleep(1)
    i+=1
