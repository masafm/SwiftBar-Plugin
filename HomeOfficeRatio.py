#!/usr/bin/env DD_LOGS_INJECTION=true DD_SERVICE=home_office_ratio DD_VERSION=1.0 DD_ENV=prod ddtrace-run python3
# <bitbar.title>HomeOfficeRatio</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Masafumi Kashiwagi</bitbar.author>
# <bitbar.author.github>masafm</bitbar.author.github>
# <bitbar.desc>Home Office Ratio</bitbar.desc>
# <bitbar.dependencies>python3</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/masafm/SwiftBar-Plugin/blob/main/HomeOfficeRatio.py</bitbar.abouturl>
# <swiftbar.type>streamable</swiftbar.type>

import signal
import sys
import subprocess
import time
import os
import requests
import logging
import json
import socket
import urllib.parse
import jpholiday
import datetime as d
from datetime import datetime, timedelta
from requests.exceptions import Timeout, RequestException
from ddtrace import tracer

INTERVAL = 600
ADDR = ['154.18.*', '209.249.*']

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
    udp_handler = UDPSocketHandler("localhost", 10518)
    udp_handler.setFormatter((UTCFormatter(FORMAT)))
    log.addHandler(udp_handler)
    return log

def exit_program(sig, frame):
    sys.exit(0)

def refresh(sig, frame):
    show_home_office_ratio()

def show_home_office_ratio():
    ratio = get_home_office_ratio()
    if(ratio):
        ratio = str(round(ratio))+'%'
    else:
        ratio = 'Err'
    print(f"""~~~
{ratio} | size=16
---
Home Office Ratio
---
Dashboard | bash='open' param1='https://masa.datadoghq.com/dashboard/hdq-kyy-3km' terminal=false""")
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


@tracer.wrap(resource="get_pip")
def get_pip():
    pip = None
    try:
        pip = requests.get("https://checkip.amazonaws.com").text.strip()
    except Exception as e:
        log.error(f"Exception: {e}", stack_info=True)

    return pip

@tracer.wrap(resource="get_home_office_ratio")
def get_home_office_ratio():
    # Get current timestamp
    cur_timestamp = int(time.time())

    # Get current IP address
    pip = get_pip()
    if(not pip):
        return None

    # Post data to Datadog API
    dd_api_key = os.getenv("DD_API_KEY")
    dd_app_key = os.getenv("DD_APP_KEY")
    ip = " OR ".join(["pip:" + item for item in ADDR])

    data = {
        "series": [
            {
             "metric": "work",
             "type": 1,
             "points": [
                 {
                  "timestamp": cur_timestamp,
                  "value": 1
                  }
                  ],
             "tags": [
                 f"pip:{pip}"
                 ]
                 }
                 ]
                 }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "DD-API-KEY": dd_api_key
        }

    today = d.date.today()
    # 曜日を取得 (月曜日が0、日曜日が6)
    weekday = today.weekday()
    # 土曜日 (5) と日曜日 (6) と祝日を除外する
    if weekday < 5 and not jpholiday.is_holiday(today):
        response = requests.post("https://api.datadoghq.com/api/v2/series", headers=headers, json=data)

    ratio = 0
    try:
        # Calculate the start and end timestamps for the current month
        first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        from_timestamp = int(first_day_of_month.timestamp())
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        to_timestamp = int(last_day_of_month.timestamp())
        log.debug(f"from: {from_timestamp}")
        log.debug(f"to: {to_timestamp}")

        # Define queries
        query_office = "count_not_null(sum:work{"+ip+"}.as_count().rollup(daily, 'Asia/Tokyo'))"
        query_home = "count_not_null(cutoff_min(sum:work{NOT ("+ip+")}.as_count().rollup(daily, 'Asia/Tokyo'), 20))"

        encoded_query_office = urllib.parse.quote(query_office)
        encoded_query_home = urllib.parse.quote(query_home)

        # Query Datadog API for office days
        response_office = requests.get(
            f"https://api.datadoghq.com/api/v1/query?from={from_timestamp}&to={to_timestamp}&query={encoded_query_office}",
            headers={
                "Accept": "application/json",
                "DD-API-KEY": dd_api_key,
                "DD-APPLICATION-KEY": dd_app_key
                }
                ).json()
        log.debug("response_office: "+str(response_office))

        # Query Datadog API for home days
        response_home = requests.get(
            f"https://api.datadoghq.com/api/v1/query?from={from_timestamp}&to={to_timestamp}&query={encoded_query_home}",
            headers={
                "Accept": "application/json",
                "DD-API-KEY": dd_api_key,
                "DD-APPLICATION-KEY": dd_app_key
                }
                ).json()
        log.debug("response_home: "+str(response_home))

        days_home = 0
        days_office = 0

        # Calculate office days
        if response_office['series']:
            for office_point in response_office['series'][0]['pointlist']:
                office_timestamp = office_point[0]
                office_value = office_point[1]

                if response_home['series']:
                    for home_point in response_home['series'][0]['pointlist']:
                        home_timestamp = home_point[0]
                        home_value = home_point[1]

                        if office_timestamp == home_timestamp:
                            if office_value > 0 and home_value > 0:
                                days_home -= 1
                                log.debug(f"{home_timestamp}: --")
                            break

                if office_value > 0:
                    days_office += 1

        # Calculate home days
        if response_home['series']:
            for home_point in response_home['series'][0]['pointlist']:
                home_value = home_point[1]

                if home_value > 0:
                    days_home += 1

        log.debug(f"Days office: {days_office}")
        log.debug(f"Days home (adjusted): {days_home}")

        ratio = 0
        # Calculate ratio
        if (days_home + days_office) == 0:
            ratio = 100
        else:
            ratio = round(days_office / (days_home + days_office) * 100, 1)
            log.debug(f"Ratio: {ratio}")

            # Post ratio data to Datadog API
            data = {
                "series": [
                    {
                     "metric": "office_percent",
                     "type": 3,
                     "points": [
                         {
                          "timestamp": cur_timestamp,
                          "value": ratio
                          }
                          ]
                          }
                          ]
                          }

            response = requests.post("https://api.datadoghq.com/api/v2/series", headers=headers, json=data)

    except Exception as e:
        log.error(f"Exception: {e}", stack_info=True)
        
    return ratio

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
    source_script('~/.env')
    resolve_and_check_connectivity("checkip.amazonaws.com")
    signal.signal(signal.SIGTERM, exit_program)
    signal.signal(signal.SIGALRM, refresh)
    signal.setitimer(signal.ITIMER_REAL, 0.1, INTERVAL)

    while True:
        time.sleep(3600)

log = get_logger()
main()
