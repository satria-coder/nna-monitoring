import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="NNA Network Monitoring", layout="wide")

DATA_FILE = "data_monitoring.csv"

# =========================
# LOAD DATA
# =========================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["Waktu Cek"])
    else:
        return pd.DataFrame(columns=[
            "Waktu Cek", "Site", "Link PTP", "Latency (ms)",
            "Packet Loss (%)", "Status Link", "Kondisi",
            "Tindakan", "PIC", "Info ke NNA"
        ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# =========================
# FUNGSI PENENTUAN KONDISI
# =========================
def get_kondisi(latency, loss, status_link):
    if status_link.lower() == "down":
        return "DOWN"
    if latency > 20 or loss > 1:
        return "MAJOR"
    if latency > 10:
        return "WARNING"
    return "NORMAL"

# =========================
# HEADER
# =========================
st.title("📡 Dashboard Monitoring Network NNA")
st.caption("Monitoring Latency PTP tiap 2 jam oleh Tim NOC")

# =========================
# FORM INPUT MONITORING
# =========================
st.subheader("➕ Input Hasil Monitoring")

with st.form("form_monitoring", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        site = st.text_input("Nama Site")
        link = st.text_input("Link PTP")

    with col2:
        latency = st.number_input("Latency (ms)", min_value=0.0, step=1.0)
        loss = st.number_input("Packet Loss (%)", min_value=0.0, step=0.1)

    with col3:
        status_link = st.selectbox("Status Link", ["UP", "FLAPPING", "DOWN", "INTERMITTENT", "HIGH-LATENCY"])
        pic = st.text_input("PIC Monitoring")

    tindakan = st.text_input("Tindakan (jika ada)")
    info_nna = st.selectbox("Sudah Info ke NNA?", ["Belum", "Sudah"])

    submit = st.form_submit_button("Simpan Data Monitoring")

    if submit:
        kondisi = get_kondisi(latency, loss, status_link)

        new_row = {
            "Waktu Cek": datetime.now(),
            "Site": site,
            "Link PTP": link,
            "Latency (ms)": latency,
            "Packet Loss (%)": loss,
            "Status Link": status_link,
            "Kondisi": kondisi,
            "Tindakan": tindakan,
            "PIC": pic,
            "Info ke NNA": info_nna
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success(f"Data tersimpan dengan kondisi: {kondisi}")

# =========================
# FILTER
# =========================
st.divider()
st.subheader("🔍 Filter Data Monitoring")

colf1, colf2 = st.columns(2)

with colf1:
    site_filter = st.multiselect("Filter Site", df["Site"].unique())

with colf2:
    kondisi_filter = st.multiselect("Filter Kondisi", df["Kondisi"].unique())

filtered_df = df.copy()

if site_filter:
    filtered_df = filtered_df[filtered_df["Site"].isin(site_filter)]

if kondisi_filter:
    filtered_df = filtered_df[filtered_df["Kondisi"].isin(kondisi_filter)]

# =========================
# STATUS SUMMARY
# =========================
st.divider()
st.subheader("📊 Ringkasan Kondisi Terakhir per Site")

if not df.empty:
    latest_status = df.sort_values("Waktu Cek").groupby("Site").tail(1)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🟢 Normal", len(latest_status[latest_status["Kondisi"] == "NORMAL"]))
    col2.metric("🟡 Warning", len(latest_status[latest_status["Kondisi"] == "WARNING"]))
    col3.metric("🔴 Major", len(latest_status[latest_status["Kondisi"] == "MAJOR"]))
    col4.metric("⚫ Down", len(latest_status[latest_status["Kondisi"] == "DOWN"]))

# =========================
# TABEL DATA
# =========================
st.divider()
st.subheader("📋 Log Monitoring")

def highlight_status(val):
    color = ""
    if val == "NORMAL":
        color = "background-color: #d4edda"
    elif val == "WARNING":
        color = "background-color: #fff3cd"
    elif val == "MAJOR":
        color = "background-color: #f8d7da"
    elif val == "DOWN":
        color = "background-color: #343a40; color: white"
    return color

if not filtered_df.empty:
    st.dataframe(
        filtered_df.sort_values("Waktu Cek", ascending=False)
        .style.applymap(highlight_status, subset=["Kondisi"]),
        use_container_width=True
    )
else:
    st.info("Belum ada data monitoring.")

# =========================
# DOWNLOAD DATA
# =========================
st.download_button(
    "⬇ Download Data Monitoring (CSV)",
    df.to_csv(index=False),
    file_name="monitoring_nna.csv",
    mime="text/csv"
)
