#!/usr/bin/env DD_LOGS_INJECTION=true DD_SERVICE=productivity DD_ENV=prod DD_VERSION=1.0 ddtrace-run python3
# <bitbar.title>Productivity</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Masafumi Kashiwagi</bitbar.author>
# <bitbar.author.github>masafm</bitbar.author.github>
# <bitbar.desc>Productivity</bitbar.desc>
# <bitbar.dependencies>python3</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/masafm/SwiftBar-Plugin/blob/main/Productivity.py</bitbar.abouturl>
# <swiftbar.type>streamable</swiftbar.type>

import signal
import sys
import subprocess
import time
import os
import requests
import logging
import socket
from urllib.parse import urlparse
from requests.exceptions import Timeout, RequestException
from ddtrace import tracer

INTERVAL = 60

class UDPSocketHandler(logging.Handler):
    def __init__(self, host, port):
        super().__init__()
        self.address = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def emit(self, record):
        try:
            msg = self.format(record)
            self.sock.sendto(msg.encode('utf-8'), self.address)
        except Exception:
            self.handleError(record)

def get_logger():
    class UTCFormatter(logging.Formatter):
        converter = time.gmtime  # Set the time conversion to UTC
    FORMAT = ('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
              '[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] '
              '- %(message)s')
    logging.basicConfig(format=FORMAT, level=logging.DEBUG, stream=sys.stdout)
    logging.getLogger().handlers[0].setFormatter(UTCFormatter(FORMAT))
    logging.getLogger().handlers[0].setLevel(logging.CRITICAL)
    log = logging.getLogger(__name__)
    udp_handler = UDPSocketHandler("localhost", 10519)
    udp_handler.setFormatter((UTCFormatter(FORMAT)))
    log.addHandler(udp_handler)
    return log

def exit_program(sig, frame):
    sys.exit(0)

def refresh(sig, frame):
    show_productivity()

def show_productivity():
    productivity = get_productivity()
    if(not productivity):
        productivity = 'Err'
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
            return None

        json_data = response.json()
        log.debug("metabase_response: "+str(json_data))

    except Timeout:
        log.warning(f"Request to {url} timed out, proceeding without data.")
        span = tracer.current_root_span()
        span.error = 0
        return None # タイムアウト時はエラーにしない
    except RequestException as e:
        log.error(f"An error occurred while connecting to Metabase: {e}")
        return None
    
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

def resolve_and_check_connectivity(hostname):
    while True:
        try:
            # 名前解決を試みる
            ip_address = socket.gethostbyname(hostname)
            log.debug(f"{hostname} resolved to {ip_address}")
            # ポート443への接続を試みる
            with socket.create_connection((ip_address, 443), timeout=5) as sock:
                log.debug(f"Successfully connected to {hostname} on port 443")
                break  # 接続が成功したらループを抜ける
        except socket.gaierror:
            # 名前解決に失敗した場合
            log.debug(f"Failed to resolve {hostname}. Retrying in 5 seconds...")
            time.sleep(5)
        except (socket.timeout, socket.error):
            # 接続に失敗した場合
            log.debug(f"Failed to connect to {hostname} on port 443. Retrying in 5 seconds...")
            time.sleep(5)

def main():
    source_script('~/src/masa-tools/profile-dd.sh')
    resolve_and_check_connectivity(urlparse(os.getenv("METABASE_URL")).netloc)
    signal.signal(signal.SIGTERM, exit_program)
    signal.signal(signal.SIGALRM, refresh)
    signal.setitimer(signal.ITIMER_REAL, 0.1, INTERVAL)

    while True:
        time.sleep(3600)

log = get_logger()
main()
