from flask import Flask, render_template, request, redirect, url_for, send_file, session, jsonify
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.util import datetime_from_timestamp
import uuid
import io
import csv
from datetime import datetime, timezone, timedelta
import logging
import os
import requests
# Import the sensor status logic
from sensor_status import sensor_statuses


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.debug = True

# Set up logging
logging.basicConfig(level=logging.INFO)

# Authentication and connection
auth_provider = PlainTextAuthProvider(username='scmcp', password='mJYcmeR7FUiFAcF7cAoN')
cluster = Cluster(['smarthomelab-cassandradb.cs.cf.ac.uk'], port=9042, auth_provider=auth_provider)
cassandra_session = cluster.connect('thingsboard')

# Simple user data for demonstration
users = {
    "admin": "admin_password",
    "user1": "password1",
    "user2": "user2password" # Add more users as needed
}
# Dictionary to store sensor statuses

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None  # Initialize the error variable
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            logging.info(f"User '{username}' logged in at {datetime.now()}")
            return redirect(url_for('index'))
        else:
            error = "Invalid Credentials"
            logging.warning(f"Failed login attempt for username: {username} at {datetime.now()}")
            return render_template('index.html', error=error)  # Pass error to the template

    return render_template('index.html', error=error)

@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Predefined device IDs list
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
        # Predefined device names and their corresponding IDs
    device_names = list(device_map.keys())
    device_ids = list(device_map.values())
    return render_template('index.html', device_names=device_names, device_ids=device_ids, device_map=device_map, sensor_statuses=sensor_statuses)


@app.route('/download', methods=['POST'])
def download_data():
    if 'username' not in session:
        return redirect(url_for('login'))

    device_ids = request.form.getlist('device_ids')
    start_datetime = request.form['start_datetime']
    end_datetime = request.form['end_datetime']

    # Convert the datetime-local input to a Python datetime object
    try:
        start_ts = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M')
        end_ts = datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M')
    except ValueError as ve:
        logging.error(f"Date parsing error: {ve}")
        return "Invalid date format", 400  # Return a 400 Bad Request

    # Ensure the datetime objects are in UTC
    start_ts = start_ts.replace(tzinfo=timezone.utc)
    end_ts = end_ts.replace(tzinfo=timezone.utc)

    if not device_ids:
        logging.warning("No device IDs selected.")
        return "No device IDs selected", 400  # Return a 400 Bad Request

    csv_data = io.StringIO()
    writer = csv.writer(csv_data)

    # Write the header with specified column names
    writer.writerow([
        "device_id", "ts", "F", "G", "H", "I", "J", "K", "L", 
        "M", "N", "O", "P", "Q", "S", "T", "U", "V", "W", 
        "X", "Y", "Z", "A1", "B1", "C1", "D1", "E1", 
        "F1", "G1", "H1", "I1", "J1", "K1", "L1"
    ])

    try:
        # Prepare the device IDs as UUID objects
        device_ids_uuids = [uuid.UUID(device_id) for device_id in device_ids]

        # Create placeholders for device IDs
        device_ids_placeholder = ', '.join(['%s'] * len(device_ids_uuids))  # Use placeholders

        # Create the query
        query = f"""
            SELECT *
            FROM thingsboard.sensor_database
            WHERE device_id IN ({device_ids_placeholder}) AND ts > %s AND ts < %s;
        """

        # Execute the query with the timestamps and UUIDs
        rows = cassandra_session.execute(query, (*device_ids_uuids, start_ts, end_ts))  # Passing UUIDs

        for row in rows:
            # Write all specified fields to CSV
            writer.writerow([
                row.device_id, row.ts, row.F, row.G, row.H, row.I, 
                row.J, row.K, row.L, row.M, row.N, row.O, 
                row.P, row.Q, row.S, row.T, row.U, row.V, 
                row.W, row.X, row.Y, row.Z, row.A1, 
                row.B1, row.C1, row.D1, row.E1, 
                row.F1, row.G1, row.H1, row.I1, 
                row.J1, row.K1, row.L1
            ])
    except Exception as e:
        logging.error(f"Error while fetching data for device IDs {device_ids}: {e}")
        return "Error fetching data", 500  # Return a 500 error if there's an issue

    csv_data.seek(0)
    return send_file(
        io.BytesIO(csv_data.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='sensor_data.csv'
    )

@app.route('/sensor-status', methods=['GET'])
def get_sensor_status():
    return jsonify(sensor_statuses)

@app.route('/logout')
def logout():
    username = session.get('username', 'Unknown user')
    logging.info(f"User '{username}' logged out at {datetime.now()}")
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/terms')
def terms():
    return render_template('terms.html')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
