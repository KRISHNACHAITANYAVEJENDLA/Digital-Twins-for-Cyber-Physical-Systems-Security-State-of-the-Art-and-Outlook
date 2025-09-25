import streamlit as st
import time
import pandas as pd
import plotly.express as px
from ingestor import ingest_data
from models import DigitalTwin

st.set_page_config(page_title="Triple Digital Twin", page_icon="🤖", layout="wide")
st.title("🚀 Triple Digital Twin (Simplified Demo)")
st.markdown("This demo simulates **sensor data** for multiple robotic arms and updates their **Digital Twin models** in real-time.")

# Initialize twins
twins = {rid: DigitalTwin(rid) for rid in ["RoboticArm_01", "RoboticArm_02"]}
history = []

placeholder = st.empty()

for i in range(30):  # simulate 30 cycles
    readings = ingest_data()

    for reading in readings:
        twins[reading["robot"]].update(reading)
        history.append(reading)

    with placeholder.container():
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔹 Latest Sensor Data")
            st.json(readings)

        with col2:
            st.subheader("🔹 Current Digital Twin States")
            for rid, twin in twins.items():
                st.write(f"**{rid}**")
                st.json(twin.get_state())

        # Chart
        df = pd.DataFrame(history)
        fig = px.line(df, x=df.index, y="temperature", color="robot", title="Temperature Trends")
        st.plotly_chart(fig, use_container_width=True)

    time.sleep(1)
