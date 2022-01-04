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
property menuTitle : "ミーティング"
property btnEnableMute : "オーディオのミュート"
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
return ""
EOF
}

function toggle_mute() {
    /usr/bin/osascript <<EOF
property menuTitle : "ミーティング"
property btnEnableMute : "オーディオのミュート"
property btnDisableMute : "オーディオのミュート解除"
if application "zoom.us" is running then
    tell application "System Events"
        tell application process "zoom.us"
            if exists (menu bar item menuTitle of menu bar 1) then
                if exists (menu item btnDisableMute of menu 1 of menu bar item menuTitle of menu bar 1) then
                    click menu item btnDisableMute of menu 1 of menu bar item menuTitle of menu bar 1
                else
                    click menu item btnEnableMute of menu 1 of menu bar item menuTitle of menu bar 1
                end if
            end if
        end tell
    end tell
end if
EOF
}

function show_mute_icon() {
    current_icon="mute"
    echo "~~~
:mic.slash.fill: | size=16
---
Zoom Mute State
ミュート解除 | bash='$0' param1=toggle_mute terminal=false"
}

function show_unmute_icon() {
    current_icon="unmute"
    echo "~~~
:mic.fill: | size=16
---
Zoom Mute State
ミュートにする | bash='$0' param1=toggle_mute terminal=false"
}

if [ "$1" == "toggle_mute" ];then
    toggle_mute
    exit
fi

function get_zoom_pid() {
    pgrep CptHost
}

trap "exit 0" 15
current_icon=""
show_mute_icon
while true;do
    if [ -n "$(get_zoom_pid)" ];then
	if [ -n "$(is_mute)" ];then
	    show_mute_icon
	else
	    show_unmute_icon
	fi
    else
	if [ $current_icon = "unmute" ];then
	    show_mute_icon
	fi
    fi
    sleep 1
done
