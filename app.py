import sqlite3
import pandas as pd
import streamlit as st
import psutil
from streamlit_autorefresh import st_autorefresh


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PC Performance Analytics",
    page_icon="💻",
    layout="wide"
)


# ============================================================
# AUTO REFRESH
# ============================================================

st_autorefresh(
    interval=5000,
    key="pc_performance_refresh"
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_PATH = "performance.db"


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


def get_tables():

    try:

        conn = get_connection()

        tables = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """,
            conn
        )

        conn.close()

        return tables["name"].tolist()

    except Exception:

        return []


def find_performance_table():

    tables = get_tables()

    if not tables:
        return None

    preferred_names = [
        "performance",
        "performance_data",
        "system_performance",
        "metrics",
        "system_metrics",
        "pc_performance",
        "monitoring"
    ]

    # Check common table names first

    for name in preferred_names:

        if name in tables:
            return name

    # Inspect table columns

    for table in tables:

        try:

            conn = get_connection()

            columns = pd.read_sql_query(
                f"PRAGMA table_info([{table}])",
                conn
            )

            conn.close()

            column_names = columns["name"].str.lower().tolist()

            performance_columns = [
                "cpu_percent",
                "ram_percent",
                "disk_percent",
                "battery_percent"
            ]

            matches = sum(
                column in column_names
                for column in performance_columns
            )

            if matches >= 2:
                return table

        except Exception:

            continue

    return tables[0]


def load_data():

    table_name = find_performance_table()

    if table_name is None:

        return None, None, "No database tables found."

    try:

        conn = get_connection()

        query = f"""
        SELECT *
        FROM [{table_name}]
        ORDER BY id ASC
        """

        df = pd.read_sql_query(
            query,
            conn
        )

        conn.close()

        return df, table_name, None

    except Exception as e:

        return None, table_name, str(e)


# ============================================================
# LOAD DATA
# ============================================================

df, table_name, db_error = load_data()


if db_error:

    st.error(
        f"Unable to read database: {db_error}"
    )

    st.stop()


if df is None or df.empty:

    st.warning(
        "The database exists, but no performance records have been collected yet."
    )

    st.info(
        "Make sure monitor.py is running."
    )

    st.stop()


# ============================================================
# NORMALIZE COLUMN NAMES
# ============================================================

df.columns = [
    str(column).strip().lower()
    for column in df.columns
]


# ============================================================
# FIND COLUMNS
# ============================================================

def find_column(possible_names):

    for name in possible_names:

        if name in df.columns:
            return name

    return None


timestamp_col = find_column([
    "timestamp",
    "time",
    "datetime",
    "recorded_at"
])

cpu_col = find_column([
    "cpu_percent",
    "cpu_usage",
    "cpu"
])

ram_col = find_column([
    "ram_percent",
    "memory_percent",
    "ram_usage",
    "memory_usage"
])

disk_col = find_column([
    "disk_percent",
    "disk_usage"
])

disk_read_col = find_column([
    "disk_read_mb",
    "disk_read",
    "read_mb"
])

disk_write_col = find_column([
    "disk_write_mb",
    "disk_write",
    "write_mb"
])

network_sent_col = find_column([
    "network_sent_mb",
    "net_sent_mb",
    "network_upload_mb"
])

network_received_col = find_column([
    "network_received_mb",
    "net_received_mb",
    "network_download_mb"
])

battery_col = find_column([
    "battery_percent",
    "battery"
])


# ============================================================
# TIMESTAMP
# ============================================================

if timestamp_col:

    df[timestamp_col] = pd.to_datetime(
        df[timestamp_col],
        errors="coerce"
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ Dashboard Controls")

time_range = st.sidebar.selectbox(
    "Select time range",
    [
        "Last 5 minutes",
        "Last 15 minutes",
        "Last 30 minutes",
        "Last 1 hour",
        "Last 6 hours",
        "Last 24 hours",
        "All data"
    ],
    index=3
)


# ============================================================
# FILTER DATA
# ============================================================

filtered_df = df.copy()


if timestamp_col and filtered_df[timestamp_col].notna().any():

    latest_time = filtered_df[timestamp_col].max()

    if time_range == "Last 5 minutes":

        start_time = latest_time - pd.Timedelta(minutes=5)

        filtered_df = filtered_df[
            filtered_df[timestamp_col] >= start_time
        ]

    elif time_range == "Last 15 minutes":

        start_time = latest_time - pd.Timedelta(minutes=15)

        filtered_df = filtered_df[
            filtered_df[timestamp_col] >= start_time
        ]

    elif time_range == "Last 30 minutes":

        start_time = latest_time - pd.Timedelta(minutes=30)

        filtered_df = filtered_df[
            filtered_df[timestamp_col] >= start_time
        ]

    elif time_range == "Last 1 hour":

        start_time = latest_time - pd.Timedelta(hours=1)

        filtered_df = filtered_df[
            filtered_df[timestamp_col] >= start_time
        ]

    elif time_range == "Last 6 hours":

        start_time = latest_time - pd.Timedelta(hours=6)

        filtered_df = filtered_df[
            filtered_df[timestamp_col] >= start_time
        ]

    elif time_range == "Last 24 hours":

        start_time = latest_time - pd.Timedelta(hours=24)

        filtered_df = filtered_df[
            filtered_df[timestamp_col] >= start_time
        ]


# ============================================================
# SAFETY CHECK
# ============================================================

if filtered_df.empty:

    st.warning(
        "No data is available for the selected time range."
    )

    st.stop()


# ============================================================
# TITLE
# ============================================================

st.title("💻 PC Performance Analytics")

st.write(
    "Real-time monitoring of CPU, RAM, disk, network and battery performance."
)


# ============================================================
# CURRENT SYSTEM STATUS
# ============================================================

st.markdown("---")

st.header("🟢 Current System Status")


latest = filtered_df.iloc[-1]


col1, col2, col3, col4 = st.columns(4)


with col1:

    if cpu_col:

        current_cpu = float(latest[cpu_col])

        st.metric(
            "CPU Usage",
            f"{current_cpu:.1f}%"
        )

    else:

        current_cpu = 0

        st.metric(
            "CPU Usage",
            "N/A"
        )


with col2:

    if ram_col:

        current_ram = float(latest[ram_col])

        st.metric(
            "RAM Usage",
            f"{current_ram:.1f}%"
        )

    else:

        current_ram = 0

        st.metric(
            "RAM Usage",
            "N/A"
        )


with col3:

    if disk_col:

        current_disk = float(latest[disk_col])

        st.metric(
            "Disk Usage",
            f"{current_disk:.1f}%"
        )

    else:

        current_disk = 0

        st.metric(
            "Disk Usage",
            "N/A"
        )


with col4:

    if battery_col:

        current_battery = float(
            latest[battery_col]
        )

        st.metric(
            "Battery",
            f"{current_battery:.0f}%"
        )

    else:

        current_battery = 0

        st.metric(
            "Battery",
            "N/A"
        )


if timestamp_col:

    latest_timestamp = latest[timestamp_col]

    if pd.notna(latest_timestamp):

        st.caption(
            f"Last recorded: {latest_timestamp}"
        )


# ============================================================
# PC HEALTH SCORE
# ============================================================

st.markdown("---")

st.header("🩺 PC Health Score")


# ------------------------------------------------------------
# Calculate health components
# ------------------------------------------------------------

health_components = []


# CPU score

if cpu_col:

    cpu_value = float(latest[cpu_col])

    if cpu_value <= 50:

        cpu_score = 100

    elif cpu_value <= 70:

        cpu_score = 85

    elif cpu_value <= 85:

        cpu_score = 65

    elif cpu_value <= 95:

        cpu_score = 40

    else:

        cpu_score = 15

    health_components.append(cpu_score)


# RAM score

if ram_col:

    ram_value = float(latest[ram_col])

    if ram_value <= 50:

        ram_score = 100

    elif ram_value <= 70:

        ram_score = 85

    elif ram_value <= 80:

        ram_score = 65

    elif ram_value <= 90:

        ram_score = 40

    else:

        ram_score = 15

    health_components.append(ram_score)


# Disk score

if disk_col:

    disk_value = float(latest[disk_col])

    if disk_value <= 50:

        disk_score = 100

    elif disk_value <= 70:

        disk_score = 85

    elif disk_value <= 85:

        disk_score = 65

    elif disk_value <= 95:

        disk_score = 40

    else:

        disk_score = 15

    health_components.append(disk_score)


# ------------------------------------------------------------
# Overall score
# ------------------------------------------------------------

if health_components:

    health_score = round(
        sum(health_components) /
        len(health_components)
    )

else:

    health_score = 0


# ------------------------------------------------------------
# Health status
# ------------------------------------------------------------

if health_score >= 85:

    health_status = "🟢 Excellent"

    health_message = (
        "Your PC is operating within a healthy performance range."
    )

elif health_score >= 70:

    health_status = "🟡 Good"

    health_message = (
        "Your PC is performing normally, with some resource usage to monitor."
    )

elif health_score >= 50:

    health_status = "🟠 Moderate"

    health_message = (
        "Some system resources are under noticeable load."
    )

else:

    health_status = "🔴 Poor"

    health_message = (
        "Your PC is experiencing high resource usage."
    )


col1, col2 = st.columns([1, 2])


with col1:

    st.metric(
        "Overall Health",
        f"{health_score}/100"
    )

    st.write(
        health_status
    )


with col2:

    st.progress(
        health_score / 100
    )

    st.write(
        health_message
    )


# ============================================================
# COMPONENT HEALTH
# ============================================================

col1, col2, col3 = st.columns(3)


with col1:

    if cpu_col:

        st.write(
            f"🔥 CPU Health: {cpu_score}/100"
        )

        st.progress(
            cpu_score / 100
        )


with col2:

    if ram_col:

        st.write(
            f"🧠 RAM Health: {ram_score}/100"
        )

        st.progress(
            ram_score / 100
        )


with col3:

    if disk_col:

        st.write(
            f"💾 Disk Health: {disk_score}/100"
        )

        st.progress(
            disk_score / 100
        )


# ============================================================
# PERFORMANCE ALERTS
# ============================================================

st.markdown("---")

st.header("🚨 Performance Alerts")


alerts_found = False


# CPU alerts

if cpu_col:

    if current_cpu >= 95:

        st.error(
            f"🔴 Critical CPU usage: {current_cpu:.1f}%"
        )

        alerts_found = True

    elif current_cpu >= 85:

        st.warning(
            f"🟠 High CPU usage: {current_cpu:.1f}%"
        )

        alerts_found = True


# RAM alerts

if ram_col:

    if current_ram >= 95:

        st.error(
            f"🔴 Critical RAM usage: {current_ram:.1f}%"
        )

        alerts_found = True

    elif current_ram >= 85:

        st.warning(
            f"🟠 High RAM usage: {current_ram:.1f}%"
        )

        alerts_found = True


# Disk alerts

if disk_col:

    if current_disk >= 95:

        st.error(
            f"🔴 Critical disk usage: {current_disk:.1f}%"
        )

        alerts_found = True

    elif current_disk >= 85:

        st.warning(
            f"🟠 High disk usage: {current_disk:.1f}%"
        )

        alerts_found = True


if not alerts_found:

    st.success(
        "✅ No critical performance issues detected."
    )


# ============================================================
# PERFORMANCE STATISTICS
# ============================================================

st.markdown("---")

st.header("📊 Performance Statistics")


col1, col2, col3, col4 = st.columns(4)


with col1:

    if cpu_col:

        avg_cpu = filtered_df[cpu_col].mean()

        st.metric(
            "Average CPU",
            f"{avg_cpu:.1f}%"
        )


with col2:

    if ram_col:

        avg_ram = filtered_df[ram_col].mean()

        st.metric(
            "Average RAM",
            f"{avg_ram:.1f}%"
        )


with col3:

    if cpu_col:

        peak_cpu = filtered_df[cpu_col].max()

        st.metric(
            "Peak CPU",
            f"{peak_cpu:.1f}%"
        )


with col4:

    if ram_col:

        peak_ram = filtered_df[ram_col].max()

        st.metric(
            "Peak RAM",
            f"{peak_ram:.1f}%"
        )


# ============================================================
# CPU CHART
# ============================================================

if cpu_col:

    st.markdown("---")

    st.header("📈 CPU Usage")

    if timestamp_col:

        chart_df = filtered_df[
            [timestamp_col, cpu_col]
        ].dropna()

        chart_df = chart_df.set_index(
            timestamp_col
        )

        st.line_chart(
            chart_df,
            y=cpu_col
        )

    else:

        st.line_chart(
            filtered_df[[cpu_col]]
        )


# ============================================================
# RAM CHART
# ============================================================

if ram_col:

    st.header("🧠 RAM Usage")

    if timestamp_col:

        chart_df = filtered_df[
            [timestamp_col, ram_col]
        ].dropna()

        chart_df = chart_df.set_index(
            timestamp_col
        )

        st.line_chart(
            chart_df,
            y=ram_col
        )

    else:

        st.line_chart(
            filtered_df[[ram_col]]
        )


# ============================================================
# DISK CHART
# ============================================================

if disk_col:

    st.header("💾 Disk Usage")

    if timestamp_col:

        chart_df = filtered_df[
            [timestamp_col, disk_col]
        ].dropna()

        chart_df = chart_df.set_index(
            timestamp_col
        )

        st.line_chart(
            chart_df,
            y=disk_col
        )

    else:

        st.line_chart(
            filtered_df[[disk_col]]
        )


# ============================================================
# DISK READ / WRITE
# ============================================================

if disk_read_col or disk_write_col:

    st.header("💿 Disk Read / Write")

    columns = []

    if disk_read_col:
        columns.append(disk_read_col)

    if disk_write_col:
        columns.append(disk_write_col)

    if timestamp_col:

        chart_df = filtered_df[
            [timestamp_col] + columns
        ].dropna(subset=[timestamp_col])

        chart_df = chart_df.set_index(
            timestamp_col
        )

        st.line_chart(
            chart_df
        )

    else:

        st.line_chart(
            filtered_df[columns]
        )


# ============================================================
# NETWORK ACTIVITY
# ============================================================

if network_sent_col or network_received_col:

    st.header("🌐 Network Activity")

    columns = []

    if network_received_col:
        columns.append(network_received_col)

    if network_sent_col:
        columns.append(network_sent_col)

    if timestamp_col:

        chart_df = filtered_df[
            [timestamp_col] + columns
        ].dropna(subset=[timestamp_col])

        chart_df = chart_df.set_index(
            timestamp_col
        )

        st.line_chart(
            chart_df
        )

    else:

        st.line_chart(
            filtered_df[columns]
        )


# ============================================================
# BATTERY
# ============================================================

if battery_col:

    st.header("🔋 Battery Level")

    if timestamp_col:

        chart_df = filtered_df[
            [timestamp_col, battery_col]
        ].dropna()

        chart_df = chart_df.set_index(
            timestamp_col
        )

        st.line_chart(
            chart_df,
            y=battery_col
        )

    else:

        st.line_chart(
            filtered_df[[battery_col]]
        )


# ============================================================
# PROCESS INTELLIGENCE
# ============================================================

st.markdown("---")

st.header("🔥 Process Intelligence")

st.write(
    "Identify which applications and background processes are consuming your PC resources."
)


process_data = []


for process in psutil.process_iter(
    [
        "pid",
        "name",
        "cpu_percent",
        "memory_percent",
        "status"
    ]
):

    try:

        info = process.info

        process_data.append({

            "PID": info["pid"],

            "Process": info["name"] or "Unknown",

            "CPU %": round(
                info["cpu_percent"] or 0,
                1
            ),

            "RAM %": round(
                info["memory_percent"] or 0,
                1
            ),

            "Status": info["status"] or "unknown"

        })

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess
    ):

        continue


process_df = pd.DataFrame(
    process_data
)


if not process_df.empty:

    top_cpu = process_df.sort_values(
        "CPU %",
        ascending=False
    ).head(10)

    top_ram = process_df.sort_values(
        "RAM %",
        ascending=False
    ).head(10)


    col1, col2 = st.columns(2)


    with col1:

        st.subheader("🔥 Top CPU Consumers")

        st.dataframe(
            top_cpu,
            use_container_width=True,
            hide_index=True
        )


    with col2:

        st.subheader("🧠 Top RAM Consumers")

        st.dataframe(
            top_ram,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# PROCESS ALERT
# ============================================================

if not process_df.empty:

    high_cpu_processes = process_df[
        process_df["CPU %"] >= 80
    ]

    if not high_cpu_processes.empty:

        st.warning(
            f"⚠️ {len(high_cpu_processes)} process(es) currently using 80%+ CPU."
        )


    high_ram_processes = process_df[
        process_df["RAM %"] >= 10
    ]

    if not high_ram_processes.empty:

        st.warning(
            f"⚠️ {len(high_ram_processes)} process(es) currently using 10%+ RAM."
        )


# ============================================================
# RECENT PERFORMANCE DATA
# ============================================================

st.markdown("---")

st.header("🕒 Recent Performance Data")


display_df = filtered_df.tail(100).copy()


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# DATABASE INFORMATION
# ============================================================

st.markdown("---")

st.header("🗄️ Database Information")


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Total Records",
        len(df)
    )


with col2:

    st.metric(
        "Displayed Records",
        len(filtered_df)
    )


with col3:

    if len(df) > 1 and timestamp_col:

        timestamps = df[
            timestamp_col
        ].dropna()

        if len(timestamps) > 1:

            intervals = (
                timestamps.diff()
                .dt.total_seconds()
            )

            median_interval = intervals.median()

            if pd.notna(median_interval):

                st.metric(
                    "Collection Interval",
                    f"{median_interval:.0f} seconds"
                )

            else:

                st.metric(
                    "Collection Interval",
                    "N/A"
                )

        else:

            st.metric(
                "Collection Interval",
                "N/A"
            )

    else:

        st.metric(
            "Collection Interval",
            "N/A"
        )


st.caption(
    f"Database table detected: {table_name}"
)