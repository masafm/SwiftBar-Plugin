#!/bin/bash
# <bitbar.title>Mic Volume</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Masafumi Kashiwagi</bitbar.author>
# <bitbar.author.github>masafm</bitbar.author.github>
# <bitbar.desc>Mic Volume</bitbar.desc>
# <bitbar.dependencies>bash,applescript,https://github.com/deweller/switchaudio-osx</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/masafm/SwiftBar-Plugin/blob/main/MicVolume.sh</bitbar.abouturl>
# <swiftbar.type>streamable</swiftbar.type>

function get_current_device() {
    SwitchAudioSource -t input -c
}

function list_input_device() {
    SwitchAudioSource -t input -a
}

function change_input_device() {
    SwitchAudioSource -t input -s "$1"
}

function get_mic_volume() {
    /usr/bin/osascript <<EOF
return input volume of (get volume settings)
EOF
}

function change_mic_volume() {
    /usr/bin/osascript <<EOF
set volume input volume $1
EOF
}

function show_mic_volume() {
    echo "~~~
$(get_current_device | cut -c 1-6)($(get_mic_volume)) | size=16
---
Mic Volume
---
マイク音量最小化(F7) | bash='$0' param1=minimize_mic_volume terminal=false shortcut=F7
マイク音量最大化(F8) | bash='$0' param1=maximize_mic_volume terminal=false shortcut=F8
---"
    list_input_device | while read line;do
	if [ "$line" != "ZoomAudioDevice" -a "$line" != "IOUSBHostInterface" ];then
	    echo "$line | bash='$0' param1=change_input_device param2='$line' terminal=false"
	fi
    done
}

if [ "$1" == "minimize_mic_volume" ];then
    change_mic_volume 0
    exit
elif [ "$1" == "maximize_mic_volume" ];then
    change_mic_volume 100
    exit
elif [ "$1" == "change_input_device" ];then
    change_input_device "$2"
    exit
fi

trap "exit 0" 15
while true;do
    show_mic_volume
    sleep 30
done
