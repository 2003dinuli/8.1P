import csv
import time
from datetime import datetime
from collections import deque
from arduino_iot_cloud import ArduinoCloudClient
import os

# Configuration
DEVICE_ID = "fe1868a9-5625-4f62-b726-e00accb4f79a"  # Your Device ID
SECRET_KEY = "QpHnqCR@3IBcb8GlSTFC6yhCu"            # Your Secret Key
CSV_FILE = "data_store.csv"                          # File to store the data
BUFFER_SIZE = 1000                                   # Buffer size before writing to CSV
SAVE_INTERVAL = 10                                   # Interval to save data in seconds

# Buffer settings
buffer = {
    'timestamp': deque(maxlen=BUFFER_SIZE),
    'py_x': deque(maxlen=BUFFER_SIZE),
    'py_y': deque(maxlen=BUFFER_SIZE),
    'py_z': deque(maxlen=BUFFER_SIZE)
}

last_save_time = time.time()

# Callback functions for sensor readings
def on_sensor_changed(axis):
    def callback(client, value):
        buffer[axis].append(value)                   # Add sensor data to buffer
        buffer['timestamp'].append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))  # Store timestamp

        # Print the latest value for debugging
        print(f"Received {axis} data: {value}")

        # Check if it's time to save data
        global last_save_time
        current_time = time.time()
        if current_time - last_save_time >= SAVE_INTERVAL:
            last_save_time = current_time
            print(f"Time interval reached. Saving data.")
            save_data()
            clear_buffer()                           # Clear buffer after saving
    return callback

def save_data():
    try:
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for i in range(len(buffer['py_x'])):      # Write all buffered data to CSV
                writer.writerow([buffer['timestamp'][i], buffer['py_x'][i], buffer['py_y'][i], buffer['py_z'][i]])
        print(f"Data saved: {len(buffer['py_x'])} readings.")
    except Exception as e:
        print(f"Error saving data: {e}")

def clear_buffer():
    buffer['py_x'].clear()
    buffer['py_y'].clear()
    buffer['py_z'].clear()
    buffer['timestamp'].clear()
    print("Buffer cleared.")

def initialize_csv():
    try:
        if not os.path.exists(CSV_FILE):             # Only initialize if file doesn't exist
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "X-axis (py_x)", "Y-axis (py_y)", "Z-axis (py_z)"])  # CSV header
            print("CSV file initialized.")
    except Exception as e:
        print(f"Error initializing CSV file: {e}")

def main():
    print("Starting the IoT client...")

    # Instantiate Arduino cloud client
    client = ArduinoCloudClient(
        device_id=DEVICE_ID, username=DEVICE_ID, password=SECRET_KEY
    )

    # Register cloud variables with corresponding callbacks
    client.register("py_x", value=None, on_write=on_sensor_changed('py_x'))
    client.register("py_y", value=None, on_write=on_sensor_changed('py_y'))
    client.register("py_z", value=None, on_write=on_sensor_changed('py_z'))

    # Initialize CSV file with headers
    initialize_csv()

    # Start the cloud client to listen for data
    client.start()

    try:
        while True:
            time.sleep(1)                            # Keep script running
    except KeyboardInterrupt:
        print("Script terminated by user.")
        if buffer['py_x']:                           # Save remaining data before exiting
            save_data()

if __name__ == "__main__":
    main()
