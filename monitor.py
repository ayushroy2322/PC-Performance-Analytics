import sqlite3
import time
from datetime import datetime

import psutil


DB_NAME = "performance.db"


def initialize_database():
    connection = sqlite3.connect(DB_NAME)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cpu_percent REAL,
            ram_percent REAL,
            disk_percent REAL,
            disk_read_mb REAL,
            disk_write_mb REAL,
            network_sent_mb REAL,
            network_received_mb REAL,
            battery_percent REAL
        )
    """)

    # Upgrade an existing database created by V1
    columns = [
        "network_sent_mb",
        "network_received_mb",
        "battery_percent"
    ]

    existing_columns = [
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(system_metrics)"
        )
    ]

    for column in columns:
        if column not in existing_columns:
            connection.execute(
                f"ALTER TABLE system_metrics ADD COLUMN {column} REAL"
            )

    connection.commit()
    connection.close()


def collect_metrics():

    cpu = psutil.cpu_percent(interval=1)

    ram = psutil.virtual_memory().percent

    disk = psutil.disk_usage("C:\\").percent

    disk_io = psutil.disk_io_counters()

    read_mb = disk_io.read_bytes / (1024 ** 2)
    write_mb = disk_io.write_bytes / (1024 ** 2)

    network = psutil.net_io_counters()

    sent_mb = network.bytes_sent / (1024 ** 2)
    received_mb = network.bytes_recv / (1024 ** 2)

    battery = psutil.sensors_battery()

    if battery:
        battery_percent = battery.percent
    else:
        battery_percent = None

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return (
        timestamp,
        cpu,
        ram,
        disk,
        read_mb,
        write_mb,
        sent_mb,
        received_mb,
        battery_percent
    )


def save_metrics(metrics):

    connection = sqlite3.connect(DB_NAME)

    connection.execute("""
        INSERT INTO system_metrics (
            timestamp,
            cpu_percent,
            ram_percent,
            disk_percent,
            disk_read_mb,
            disk_write_mb,
            network_sent_mb,
            network_received_mb,
            battery_percent
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, metrics)

    connection.commit()
    connection.close()


if __name__ == "__main__":

    initialize_database()

    print("=" * 50)
    print("       PC PERFORMANCE ANALYTICS")
    print("=" * 50)
    print("Collecting system data every 5 seconds.")
    print("Press CTRL+C to stop.")
    print()

    while True:

        try:

            metrics = collect_metrics()

            save_metrics(metrics)

            battery_text = (
                f"{metrics[8]:.0f}%"
                if metrics[8] is not None
                else "N/A"
            )

            print(
                f"{metrics[0]} | "
                f"CPU: {metrics[1]:5.1f}% | "
                f"RAM: {metrics[2]:5.1f}% | "
                f"Disk: {metrics[3]:5.1f}% | "
                f"Battery: {battery_text}"
            )

            time.sleep(5)

        except KeyboardInterrupt:

            print("\nMonitoring stopped.")
            break