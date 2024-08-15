import threading
from datetime import datetime, timezone, timedelta
import requests
import logging

# Dictionary to store sensor statuses
sensor_statuses = {}

# Function to fetch sensor status
def fetch_sensor_status():
    global sensor_statuses

    device_map = {
        "sensor_node_01": "70ad22a0-b82c-11ed-b196-bb47e24272bc",
        "sensor_node_02": "75d29440-b82c-11ed-b196-bb47e24272bc",
        "sensor_node_04": "a673eb80-b82c-11ed-b196-bb47e24272bc",
        "sensor_node_05": "83456b70-b82c-11ed-b196-bb47e24272bc",
        "sensor_node_06": "b96d6720-b82c-11ed-b196-bb47e24272bc",
        "sensor_node_07": "be98a520-b82c-11ed-b196-bb47e24272bc",
        "sensor_node_08": "c3110de0-b82c-11ed-b196-bb47e24272bc",
        "sensor_node_09": "c950f030-b82c-11ed-b196-bb47e24272bc",
        "sensor_node_10": "cfddba00-b82c-11ed-b196-bb47e24272bc",
        "sensor_node_11": "278505c0-0f7a-11ee-bf90-a16a1a9e1e0a",
        "sensor_node_12": "d9576a90-b82c-11ed-b196-bb47e24272bc",
        "sensor_node_13": "de18ea40-b82c-11ed-b196-bb47e24272bc",
        "sensor_node_14": "f57a1560-7cf3-11ee-94bc-d389020903a3",
        "sensor_node_15": "508d1b60-57eb-11ee-8714-19d56ba0c4fd",
        "sensor_node_16": "86c63bd0-57f0-11ee-8714-19d56ba0c4fd",
        "sensor_node_17": "3efd82d0-7cf4-11ee-94bc-d389020903a3",
        "sensor_node_18": "f583bc50-57e6-11ee-8714-19d56ba0c4fd",
        "sensor_node_19": "9458c560-0f75-11ee-bf90-a16a1a9e1e0a",
        "sensor_node_21": "2ae959b0-53c6-11ee-8714-19d56ba0c4fd",
        "sensor_node_22": "351b0eb0-57ef-11ee-8714-19d56ba0c4fd",
        "sensor_node_23": "0f96bed0-b82d-11ed-b196-bb47e24272bc",
        "sensor_node_24": "13e642d0-b82d-11ed-b196-bb47e24272bc",
        "sensor_node_25": "18a159e0-b82d-11ed-b196-bb47e24272bc",
        "sensor_node_26": "fef50770-57f1-11ee-8714-19d56ba0c4fd",
        "sensor_node_27": "2a5d9a90-b82d-11ed-b196-bb47e24272bc",
        "sensor_node_28": "99c6a3b0-b82b-11ed-b196-bb47e24272bc",
        "sensor_node_29": "51f2d170-57e1-11ee-8714-19d56ba0c4fd",
        "sensor_node_30": "9c563630-0f75-11ee-bf90-a16a1a9e1e0a",
        "sensor_node_31": "391303e0-b82d-11ed-b196-bb47e24272bc",
        "sensor_node_32": "3d3a3f60-b82d-11ed-b196-bb47e24272bc",
        "sensor_node_34": "4665a8e0-b82d-11ed-b196-bb47e24272bc",
        "sensor_node_35": "b9cb09a0-11ec-11ef-b56b-a96a8be1c6f5"
    }

    # Authenticate with the ThingsBoard API
    url = "https://thingsboard.cs.cf.ac.uk/api/auth/login"
    headers = {"Content-Type": "application/json"}
    payload = {
        "username": "SuhasAbacwsLivingLab@cardiff.ac.uk",
        "password": "SuhasDevmane"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        token = response.json().get("token")
        logging.info("Successfully authenticated with JWT Token.")

        keys_to_fetch = ["ip_address"]

        for sensor_name, device_id in device_map.items():
            telemetry_url = f"https://thingsboard.cs.cf.ac.uk/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries?keys={','.join(keys_to_fetch)}"
            headers = {
                "Content-Type": "application/json",
                "X-Authorization": f"Bearer {token}",
            }

            telemetry_response = requests.get(telemetry_url, headers=headers)

            if telemetry_response.status_code == 200:
                data = telemetry_response.json()
                ts = None

                if "ip_address" in data and data["ip_address"]:
                    ts = data["ip_address"][0]['ts']  # Get the timestamp

                if ts:
                    ts_datetime = datetime.fromtimestamp(ts / 1000, timezone.utc)
                    current_time = datetime.now(timezone.utc)

                    if current_time - ts_datetime <= timedelta(minutes=5):
                        sensor_statuses[sensor_name] = "Online"
                    else:
                        sensor_statuses[sensor_name] = "Offline"
                else:
                    sensor_statuses[sensor_name] = "Offline"
            else:
                sensor_statuses[sensor_name] = "Offline"
    else:
        logging.error(f"Authentication failed. Status Code: {response.status_code}")

    logging.info(f"Sensor statuses updated: {sensor_statuses}")
    
    # Schedule the next status check in 5 minutes
    threading.Timer(300, fetch_sensor_status).start()

# Start the initial sensor status fetch in a separate thread
def start_sensor_status_fetch():
    thread = threading.Thread(target=fetch_sensor_status)
    thread.daemon = True  # Daemonize thread to exit when the main program exits
    thread.start()

# Call this function in your Flask application or main script to start fetching statuses
start_sensor_status_fetch()

# sensor_statuses will be updated every 5 minutes in the background.
