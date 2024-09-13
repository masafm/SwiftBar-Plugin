#!/usr/bin/env DD_SERVICE=productivity DD_ENV=prod DD_VERSION=1.0 ddtrace-run python3
# <bitbar.title>Productivity</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Masafumi Kashiwagi</bitbar.author>
# <bitbar.author.github>masafm</bitbar.author.github>
# <bitbar.desc>Productivity</bitbar.desc>
# <bitbar.dependencies>python3</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/masafm/SwiftBar-Plugin/blob/main/ZoomMuteState.sh</bitbar.abouturl>
# <swiftbar.type>streamable</swiftbar.type>

import signal
import sys
import subprocess
import time
import os
import requests
import logging
from requests.exceptions import Timeout, RequestException
from ddtrace import tracer

INTERVAL=60

def get_logger():
    log = logging.getLogger(__name__)
    log.level = logging.CRITICAL
    return log

log = get_logger()

def exit_program(sig, frame):
    sys.exit(0)

def refresh(sig, frame):
    show_productivity()

def show_productivity():
    productivity = float(get_productivity())
    print(f"""~~~
{productivity} | size=16
---
Productivity
---
Dashboard | bash='open' param1='https://masa.datadoghq.com/dashboard/wyw-exk-5wc' terminal=false""")
    sys.stdout.flush()

@tracer.wrap(resource="source_script")
def source_script(script_path):
    # ファイルの存在を確認
    expanded_path = os.path.expanduser(script_path)
    if os.path.exists(expanded_path):
        # シェルスクリプトをサブシェルで実行し、環境変数をキャプチャ
        command = f"source {expanded_path} && env"
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable='/bin/zsh')
        for line in proc.stdout:
            # 各行を分割して環境変数を取得
            (key, _, value) = line.decode('utf-8').partition("=")
            os.environ[key] = value.strip()
        proc.communicate()

@tracer.wrap(resource="get_productivity")
def get_productivity():
    # Check if the profile script exists and source it
    source_script('~/src/masa-tools/profile-dd.sh')

    # Get current timestamp
    cur_timestamp = int(time.time())

    url = os.getenv("METABASE_URL")

    # 環境変数からクッキーを取得
    cookie = os.getenv("METABASE_COOKIE")
    
    headers = {
        "accept": "application/json",
        "accept-language": "ja,en-US;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "cookie": cookie,
        "pragma": "no-cache",
        }

    data = {
        "parameters": "[]"
    }

    try:
        # POSTリクエストを送信し、タイムアウトは許容
        response = requests.post(url, headers=headers, data=data, timeout=10)

        # ステータスコードのチェック
        if response.status_code // 100 != 2:
            log.error(f"Failed to retrieve data from Metabase. HTTP Status Code: {response.status_code}")
            return -1

        json_data = response.json()
        log.debug("metabase_response: "+str(json_data))

    except Timeout:
        log.warning(f"Request to {url} timed out, proceeding without data.")
        span = tracer.current_root_span()
        span.error = 0
        return -1 # タイムアウト時はエラーにしない
    except RequestException as e:
        log.error(f"An error occurred while connecting to Metabase: {e}")
        return -1  # 例外を再スロー
    
    # Post data to Datadog API
    dd_api_key = os.getenv("DD_API_KEY")
    dd_app_key = os.getenv("DD_APP_KEY")

    data = {"series": []}
    my_productivity=None
    for person_data in json_data:
        name = person_data["Name"]
        zendesk_id = person_data["Zendesk ID"]
        productivity = person_data.get("Productivity")
        productivity_weighted = person_data.get("Weighted Productivity")
        solved_tickets = person_data.get("Solved Tickets")
        solved_tickets_target = person_data.get("Solved Tickets Target")
            
        if productivity is None:
            continue    
        # Datadogに送信するデータの作成
        data["series"].append(
            {
             "metric": "productivity",
             "type": 3,
             "points": [
                 {
                  "timestamp": cur_timestamp,
                  "value": float(productivity)
                  },
                  ],
             "tags": [f"name:{name}",f"zendesk_id:{zendesk_id}"]
             }
        )
        if productivity_weighted is None:
            continue    
        data["series"].append(
            {
             "metric": "productivity.weighted",
             "type": 3,
             "points": [
                 {
                  "timestamp": cur_timestamp,
                  "value": float(productivity_weighted)
                  },
                  ],
             "tags": [f"name:{name}",f"zendesk_id:{zendesk_id}"]
             }
        )
        if solved_tickets is None:
            continue    
        data["series"].append(
            {
             "metric": "solved_tickets",
             "type": 1,
             "points": [
                 {
                  "timestamp": cur_timestamp,
                  "value": float(solved_tickets)
                  },
                  ],
             "tags": [f"name:{name}",f"zendesk_id:{zendesk_id}"]
             }
        )
        if solved_tickets_target is None:
            continue    
        data["series"].append(
            {
             "metric": "solved_tickets.target",
             "type": 1,
             "points": [
                 {
                  "timestamp": cur_timestamp,
                  "value": float(solved_tickets_target)
                  },
                  ],
             "tags": [f"name:{name}",f"zendesk_id:{zendesk_id}"]
             }
        )

        if name == 'Masafumi Kashiwagi':
            my_productivity = float(solved_tickets) - float(solved_tickets_target)
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "DD-API-KEY": dd_api_key
        }

    # DatadogにPOSTリクエストを送信
    response = requests.post("https://api.datadoghq.com/api/v2/series", headers=headers, json=data)

    # レスポンスを確認
    if response.status_code == 202:
        log.info(f"Successfully sent metrics")
    else:
        log.error(f"Failed to send metrics. Response: {response.text}")

    return my_productivity

def main():
    signal.signal(signal.SIGTERM, exit_program)
    signal.signal(signal.SIGALRM, refresh)
    signal.setitimer(signal.ITIMER_REAL, 0.1, INTERVAL)

    while True:
        time.sleep(3600)

main()
