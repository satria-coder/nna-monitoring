import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

st.set_page_config(page_title="NNA Network Monitoring", layout="wide")

DATA_FILE = "data_monitoring.csv"

COLUMNS = [
    "Waktu Cek", "Site", "Link PTP", "Latency (ms)",
    "Packet Loss (%)", "Status Link", "Kondisi",
    "Tindakan", "PIC", "Info ke NNA"
]

# =========================
# LOAD DATA AMAN
# =========================
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=COLUMNS)

    if os.path.getsize(DATA_FILE) == 0:
        return pd.DataFrame(columns=COLUMNS)

    try:
        df = pd.read_csv(DATA_FILE)

        if not set(COLUMNS).issubset(df.columns):
            return pd.DataFrame(columns=COLUMNS)

        df["Waktu Cek"] = pd.to_datetime(df["Waktu Cek"], errors="coerce")
        df["Latency (ms)"] = pd.to_numeric(df["Latency (ms)"], errors="coerce").fillna(0).astype(int)
        df["Packet Loss (%)"] = pd.to_numeric(df["Packet Loss (%)"], errors="coerce").fillna(0).astype(int)
        return df

    except Exception:
        st.warning("File data rusak/kosong. Sistem membuat data baru.")
        return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# Pastikan kolom waktu valid
if "Waktu Cek" in df.columns:
    df["Waktu Cek"] = pd.to_datetime(df["Waktu Cek"], errors="coerce")

# =========================
# LOGIC STATUS KONDISI
# =========================
def get_kondisi(latency, loss, status_link):
    status_link = status_link.lower()

    if status_link == "down":
        return "DOWN"

    if status_link == "intermittent":
        return "MAJOR"

    if latency > 20:
        return "HIGH LATENCY"

    if loss > 1:
        return "MAJOR"

    if latency > 10:
        return "WARNING"

    return "NORMAL"

# =========================
# HEADER
# =========================
st.title("📡 Dashboard Monitoring Network NNA")
st.caption("Monitoring Latency PTP Tiap 2 Jam oleh Tim NOC (WIB)")

# =========================
# FORM INPUT
# =========================
st.subheader("➕ Input Hasil Monitoring")

with st.form("form_monitoring", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        site = st.text_input("Nama Site")
        link = st.text_input("Link PTP")

    with col2:
        latency = st.number_input("Latency (ms)", min_value=0, step=1, format="%d")
        loss = st.number_input("Packet Loss (%)", min_value=0, step=1, format="%d")

    with col3:
        status_link = st.selectbox("Status Link", ["UP", "FLAPPING", "INTERMITTENT", "DOWN"])
        pic = st.text_input("PIC Monitoring")

    tindakan = st.text_input("Tindakan (jika ada)")
    info_nna = st.selectbox("Sudah Info ke NNA?", ["Belum", "Sudah"])

    submit = st.form_submit_button("Simpan Data Monitoring")

    if submit:
        if site.strip() == "":
            st.warning("Nama site wajib diisi")
        else:
            kondisi = get_kondisi(int(latency), int(loss), status_link)

            WIB = timezone(timedelta(hours=7))
            waktu_wib = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")

            new_row = {
                "Waktu Cek": waktu_wib,
                "Site": site,
                "Link PTP": link,
                "Latency (ms)": int(latency),
                "Packet Loss (%)": int(loss),
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
    site_filter = st.multiselect("Filter Site", sorted(df["Site"].dropna().unique()))

with colf2:
    kondisi_filter = st.multiselect("Filter Kondisi", sorted(df["Kondisi"].dropna().unique()))

filtered_df = df.copy()

if site_filter:
    filtered_df = filtered_df[filtered_df["Site"].isin(site_filter)]

if kondisi_filter:
    filtered_df = filtered_df[filtered_df["Kondisi"].isin(kondisi_filter)]

# =========================
# RINGKASAN STATUS TERAKHIR
# =========================
st.divider()
st.subheader("📊 Status Terakhir per Site")

valid_df = df.dropna(subset=["Waktu Cek"])

if not valid_df.empty:
    latest_status = valid_df.sort_values("Waktu Cek").groupby("Site").tail(1)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🟢 Normal", len(latest_status[latest_status["Kondisi"] == "NORMAL"]))
    col2.metric("🟡 Warning", len(latest_status[latest_status["Kondisi"] == "WARNING"]))
    col3.metric("🟠 High Latency", len(latest_status[latest_status["Kondisi"] == "HIGH LATENCY"]))
    col4.metric("🔴 Major", len(latest_status[latest_status["Kondisi"] == "MAJOR"]))
    col5.metric("⚫ Down", len(latest_status[latest_status["Kondisi"] == "DOWN"]))
else:
    st.info("Belum ada data monitoring valid.")

# =========================
# WARNA KONDISI
# =========================
def highlight_status(val):
    if val == "NORMAL":
        return "background-color: #d4edda"
    if val == "WARNING":
        return "background-color: #fff3cd"
    if val == "HIGH LATENCY":
        return "background-color: #ffe5b4"
    if val == "MAJOR":
        return "background-color: #f8d7da"
    if val == "DOWN":
        return "background-color: #343a40; color: white"
    return ""

# =========================
# TABEL DATA
# =========================
st.divider()
st.subheader("📋 Log Monitoring")

if not filtered_df.empty:
    st.dataframe(
        filtered_df.sort_values("Waktu Cek", ascending=False)
        .style.applymap(highlight_status, subset=["Kondisi"]),
        use_container_width=True
    )
else:
    st.info("Belum ada data monitoring sesuai filter.")

# =========================
# DOWNLOAD
# =========================
st.download_button(
    "⬇ Download Data Monitoring (CSV)",
    df.to_csv(index=False),
    file_name="monitoring_nna.csv",
    mime="text/csv"
)
