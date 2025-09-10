import streamlit as st
import requests

# import time
# from datetime import date
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Tra thông tin đất", layout="wide")
API_BASE = st.secrets.get("API_BASE", "http://localhost:8000")


# Handle error function
def error_toast(msg: str):
    st.toast(msg)


def success_toast(msg: str):
    st.toast(msg)


# ===== Load Data =====
def load_city_map():
    try:
        res = requests.get(f"{API_BASE}/get_city_map")
        res.raise_for_status()
        city_map = res.json()
        return city_map
    except requests.exceptions.HTTPError as e:
        msg = str(e)
        error_toast(f"{msg}")
        return {}
    except Exception as e:
        error_toast(f"Error loading city map: {e}")
        return {}


city_map = load_city_map()
cities = sorted(city_map.keys())
pcities = sorted(city_map.keys())


# ===== Callback =====
# Định giá
def update_districts():
    city = st.session_state.city
    st.session_state.districts = sorted(city_map[city].keys())
    st.session_state.district = None
    st.session_state.wards = []
    st.session_state.ward = None
    st.session_state.streets = []
    st.session_state.street = None
    update_area()


def update_wards():
    city = st.session_state.city
    district = st.session_state.district
    st.session_state.wards = sorted(city_map[city][district])
    st.session_state.ward = None
    st.session_state.streets = []
    st.session_state.street = None
    update_area()


def update_streets():
    city = st.session_state.city
    district = st.session_state.district
    ward = st.session_state.ward
    st.session_state.streets = sorted(city_map[city][district][ward])
    st.session_state.street = None
    update_area()


def update_area():
    st.session_state.land_area = 0.0


# Dự báo
def pupdate_districts():
    city = st.session_state.pcity
    st.session_state.pdistricts = sorted(city_map[city].keys())
    st.session_state.pdistrict = None
    st.session_state.pwards = []
    st.session_state.pward = None
    st.session_state.pstreets = []
    st.session_state.pstreet = None
    pupdate_area()


def pupdate_wards():
    city = st.session_state.pcity
    district = st.session_state.pdistrict
    st.session_state.pwards = sorted(city_map[city][district])
    st.session_state.pward = None
    st.session_state.pstreets = []
    st.session_state.pstreet = None
    pupdate_area()


def pupdate_area():
    st.session_state.pland_area = 0.0


# ===== Initialization session state =====
# Định giá
if "city" not in st.session_state:
    st.session_state.city = None
if "districts" not in st.session_state:
    st.session_state.districts = []
if "district" not in st.session_state:
    st.session_state.district = None
if "wards" not in st.session_state:
    st.session_state.wards = []
if "ward" not in st.session_state:
    st.session_state.ward = None
if "streets" not in st.session_state:
    st.session_state.streets = []
if "street" not in st.session_state:
    st.session_state.street = None
if "land_area" not in st.session_state:
    st.session_state.land_area = 0.0

# Dự báo
if "pcity" not in st.session_state:
    st.session_state.pcity = None
if "pdistricts" not in st.session_state:
    st.session_state.pdistricts = []
if "pdistrict" not in st.session_state:
    st.session_state.pdistrict = None
if "pwards" not in st.session_state:
    st.session_state.pwards = []
if "pward" not in st.session_state:
    st.session_state.pward = None
if "pland_area" not in st.session_state:
    st.session_state.pland_area = 0.0

# Tab 1: Định giá nhà đất
tab1, tab2 = st.tabs(["🏠 Tra thông tin đất", "📈 Dự báo nhà đất"])
with tab1:
    st.title("🏠 Nhập thông tin thửa đất")

    # ===== Form Input =====
    st.selectbox(
        "Thành phố",
        options=cities,
        key="city",
        index=None,
        on_change=update_districts,
        placeholder="Chọn thành phố",
    )

    st.selectbox(
        "Quận/Huyện",
        options=st.session_state.districts,
        key="district",
        index=None,
        on_change=update_wards,
        placeholder="Chọn quận/huyện",
    )

    st.selectbox(
        "Phường/Xã",
        options=st.session_state.wards,
        key="ward",
        index=None,
        on_change=update_streets,
        placeholder="Chọn phường/xã",
    )

    st.selectbox(
        "Đường",
        options=st.session_state.streets,
        key="street",
        index=None,
        on_change=update_area,
        placeholder="Chọn đường",
    )
    land_area = st.number_input("Diện tích đất (m²)", format="%.2f", key="land_area")

    # ===== Submit =====
    submitted = st.button("Gửi", key="Dinh_gia")

    if submitted:
        errors = []
        if not st.session_state.city:
            errors.append("Thành phố không được để trống.")
        if not st.session_state.district:
            errors.append("Quận/Huyện không được để trống.")
        if not st.session_state.ward:
            errors.append("Phường/Xã không được để trống.")
        if not st.session_state.street:
            errors.append("Đường không được để trống.")
        if st.session_state.land_area <= 0:
            errors.append("Diện tích đất không được để trống.")

        if errors:
            error_toast(errors[0])
        else:
            try:
                success_toast("Gửi thành công!")
                payload = {
                    "city": st.session_state.city,
                    "district": st.session_state.district,
                    "ward": st.session_state.ward,
                    "street": st.session_state.street,
                    "land_area": float(st.session_state.land_area),
                }
                try:
                    r = requests.post(f"{API_BASE}/estimate_cost", json=payload)
                    r.raise_for_status()
                    data = r.json()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Địa chỉ**")
                        st.write(
                            f"{st.session_state.street}, {st.session_state.district}, {st.session_state.city}"
                        )
                        st.write(f"**Diện tích:** {st.session_state.land_area} m²")
                    with col2:
                        st.write("**Ước tính (minh hoạ)**")
                        st.write(f"Đơn giá: {data['Don gia']:,} đ/m²")
                        st.write(f"Estimate: **{data['Gia']:,} đ**")
                    st.caption(data.get("note", ""))

                except requests.exceptions.HTTPError as e:
                    msg = str(e)
                    error_toast(f"Lỗi: {msg}")

            except Exception as e:
                error_toast(f"Lỗi gọi API: {e}")
# Tab 2: Dự báo nhà đất
with tab2:
    st.title("📈 Dự báo nhà đất")

    # ===== Form Input =====
    st.selectbox(
        "Thành phố",
        options=pcities,
        key="pcity",
        index=None,
        on_change=pupdate_districts,
        placeholder="Chọn thành phố",
    )

    st.selectbox(
        "Quận/Huyện",
        options=st.session_state.pdistricts,
        key="pdistrict",
        index=None,
        on_change=pupdate_wards,
        placeholder="Chọn quận/huyện",
    )

    st.selectbox(
        "Phường/Xã",
        options=st.session_state.pwards,
        key="pward",
        index=None,
        on_change=pupdate_area,
        placeholder="Chọn phường/xã",
    )

    land_area = st.number_input("Diện tích đất (m²)", format="%.2f", key="pland_area")

    # ===== Submit =====
    submitted = st.button("Gửi", key="Du bao")
    if submitted:
        errors = []
        if not st.session_state.pcity:
            errors.append("Thành phố không được để trống.")
        if not st.session_state.pdistrict:
            errors.append("Quận/Huyện không được để trống.")
        if not st.session_state.pward:
            errors.append("Phường/Xã không được để trống.")
        if st.session_state.pland_area <= 0:
            errors.append("Diện tích đất không được để trống.")

        if errors:
            error_toast(errors[0])
        else:
            try:
                success_toast("Gửi thành công!")
                payload = {
                    "city": st.session_state.pcity,
                    "district": st.session_state.pdistrict,
                    "ward": st.session_state.pward,
                    "land_area": float(st.session_state.pland_area),
                }
                try:
                    r = requests.post(f"{API_BASE}/predict", json=payload)
                    r.raise_for_status()
                    data = r.json()

                    df = pd.DataFrame(
                        {
                            "Thời gian": data["timeline"][-3:],
                            "Giá trị dự đoán": [
                                "{:,}".format(val * st.session_state.pland_area)
                                for val in data["predictions"]
                            ],
                        }
                    )
                    st.write(
                        f"Bảng dự đoán giá nhà đất tại {st.session_state.pward} sau 3 tháng"
                    )
                    st.dataframe(df)
                    st.write(f"Biểu đồ dự báo giá nhà đất tại {st.session_state.pward}")
                    st.write(data["timeline"])

                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=data["timeline"],
                            y=data["true"],
                            mode="lines+markers",
                            name="Thực tế",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=data["timeline"],
                            y=data["predictions"],
                            mode="lines+markers",
                            name="Dự đoán + Tương lai",
                        )
                    )

                    fig.update_layout(
                        xaxis_title="Thời gian",
                        yaxis_title="Giá trị (m2)",
                        template="plotly_white",
                    )

                    st.plotly_chart(fig, use_container_width=True)

                except requests.exceptions.HTTPError as e:
                    msg = str(e)
                    error_toast(f"Lỗi: {msg}")

            except Exception as e:
                error_toast(f"Lỗi gọi API: {e}")
