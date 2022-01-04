#!/bin/bash
# <bitbar.title>Zoom Mute State</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Masafumi Kashiwagi</bitbar.author>
# <bitbar.author.github>masafm</bitbar.author.github>
# <bitbar.desc>Zoom Mute State</bitbar.desc>
# <bitbar.dependencies>bash,applescript</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/masafm/SwiftBar-Plugin/blob/main/ZoomMuteState.sh</bitbar.abouturl>
# <swiftbar.type>streamable</swiftbar.type>

function is_mute() {
    /usr/bin/osascript <<EOF
property btnTitle : "オーディオのミュート解除"
if application "zoom.us" is running then
    tell application "System Events"
        tell application process "zoom.us"
            if exists (menu bar item "ミーティング" of menu bar 1) then
                if exists (menu item btnTitle of menu 1 of menu bar item "ミーティング" of menu bar 1) then
                    return 1
                end if
            end if
        end tell
    end tell
end if
return ""
EOF
}

function toggle_mute() {
    /usr/bin/osascript <<EOF
if application "zoom.us" is running then
    tell application "System Events"
        tell application process "zoom.us"
            keystroke (ASCII character 16)#Press F1 key
        end tell
    end tell
end if
EOF
}

function show_mute_icon() {
	echo "~~~
:mic.slash.fill: | size=16
---
ミュート解除 | bash='$0' param1=toggle_mute terminal=false"
}

function show_unmute_icon() {
    echo "~~~
:mic.fill: | size=16
---
ミュートにする | bash='$0' param1=toggle_mute terminal=false"
}

if [ "$1" == "toggle_mute" ];then
    toggle_mute
    exit
fi

while true;do
    if [ -n "$(pgrep CptHost)" ];then
	if [ -n "$(is_mute)" ];then
	    show_mute_icon
	else
	    show_unmute_icon
	fi
    else
	show_mute_icon
    fi
    sleep 1	
done
