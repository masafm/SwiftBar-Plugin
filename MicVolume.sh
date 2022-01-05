#!/bin/bash
# <bitbar.title>Mic Volume</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Masafumi Kashiwagi</bitbar.author>
# <bitbar.author.github>masafm</bitbar.author.github>
# <bitbar.desc>Mic Volume</bitbar.desc>
# <bitbar.dependencies>bash,applescript</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/masafm/SwiftBar-Plugin/blob/main/MicVolume.sh</bitbar.abouturl>
# <swiftbar.type>streamable</swiftbar.type>

function get_mic_volume() {
    /usr/bin/osascript <<EOF
return input volume of (get volume settings)
EOF
}

function maximize_mic_volume() {
    /usr/bin/osascript <<EOF
set volume input volume 100
EOF
}

function show_mic_volume() {
    echo "~~~
$(get_mic_volume) | size=16
---
Mic Volume
マイク音量最大化 | bash='$0' param1=maximize_mic_volume terminal=false"
}

if [ "$1" == "maximize_mic_volume" ];then
    maximize_mic_volume
    exit
fi

trap "exit 0" 15
while true;do
    show_mic_volume
    sleep 1
done
