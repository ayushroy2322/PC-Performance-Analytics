import sqlite3
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="PC Performance Analytics",
    page_icon="💻",
    layout="wide"
)


@st.fragment(run_every="5s")
def dashboard():

    connection = sqlite3.connect("performance.db")

    df = pd.read_sql_query(
        """
        SELECT *
        FROM system_metrics
        ORDER BY timestamp
        """,
        connection
    )

    connection.close()

    if df.empty:
        st.warning("No performance data available yet.")
        return

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Latest reading
    latest = df.iloc[-1]

    # Header
    st.title("💻 PC Performance Analytics")
    st.caption("Real-time system performance monitoring")

    st.success(
        f"Monitoring active • {len(df)} records collected"
    )

    # Current metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "CPU Usage",
            f"{latest['cpu_percent']:.1f}%"
        )

    with col2:
        st.metric(
            "RAM Usage",
            f"{latest['ram_percent']:.1f}%"
        )

    with col3:
        st.metric(
            "Disk Usage",
            f"{latest['disk_percent']:.1f}%"
        )

    with col4:
        if "battery_percent" in df.columns:
            st.metric(
                "Battery",
                f"{latest['battery_percent']:.0f}%"
            )

    st.divider()

    # CPU chart
    st.subheader("📈 CPU Usage")

    cpu_chart = df.set_index("timestamp")[["cpu_percent"]]

    st.line_chart(
        cpu_chart,
        height=300
    )

    # RAM chart
    st.subheader("🧠 RAM Usage")

    ram_chart = df.set_index("timestamp")[["ram_percent"]]

    st.line_chart(
        ram_chart,
        height=300
    )

    # Disk chart
    st.subheader("💾 Disk Usage")

    disk_chart = df.set_index("timestamp")[["disk_percent"]]

    st.line_chart(
        disk_chart,
        height=300
    )

    st.divider()

    # Statistics
    st.subheader("📊 Performance Statistics")

    stat1, stat2, stat3 = st.columns(3)

    with stat1:
        st.metric(
            "Average CPU",
            f"{df['cpu_percent'].mean():.1f}%"
        )

    with stat2:
        st.metric(
            "Average RAM",
            f"{df['ram_percent'].mean():.1f}%"
        )

    with stat3:
        st.metric(
            "Peak CPU",
            f"{df['cpu_percent'].max():.1f}%"
        )

    st.divider()

    # Recent data
    st.subheader("🕐 Recent Performance Data")

    st.dataframe(
        df.tail(20),
        use_container_width=True,
        hide_index=True
    )


dashboard()