from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
import json
from pathlib import Path
from utils.city_map_shape import city_map_shape
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet
import torch
from sklearn.preprocessing import LabelEncoder, StandardScaler
from model.landTransformer import Stockformer

# ===== Connect MongoDB =====
load_dotenv()
MONGODB_URI = os.getenv("URI")
MONGODB_DB = os.getenv("DB")


# ===== Async MongoDB Client =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MONGODB_DB:
        raise RuntimeError("Environment variable 'DB' is not set or is empty.")
    app.state.mongo_client = AsyncIOMotorClient(MONGODB_URI)
    app.state.db = app.state.mongo_client[MONGODB_DB]
    yield
    app.state.mongo_client.close()


# ===== CORS =====
app = FastAPI(title="QUIN Backend API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Models =====
class PropertyIn(BaseModel):
    city: str = Field(..., min_length=1)
    district: str = Field(..., min_length=1)
    ward: str = Field(..., min_length=1)
    street: Optional[str] = Field(None, min_length=1)
    land_area: float = Field(..., gt=0, description="m2")


# ===== Routes =====


# Get city map
@app.get("/get_city_map")
async def get_city_map():
    try:
        cursor = app.state.db.city_map.find({}, {"_id": 0})
        docs = await cursor.to_list(length=None)

        if not docs:
            raise HTTPException(status_code=404, detail="City map not found")

        merged: Dict[str, Dict[str, Dict[str, List[str]]]] = {}
        for doc in docs:
            for city, dist_obj in doc.items():
                if city.startswith("_"):
                    continue
                merged.setdefault(city, {})
                if not isinstance(dist_obj, dict):
                    continue
                for dist, ward_obj in dist_obj.items():
                    merged[city].setdefault(dist, {})
                    if not isinstance(ward_obj, dict):
                        continue
                    for ward, streets in ward_obj.items():
                        merged[city][dist].setdefault(ward, [])
                        if isinstance(streets, list):
                            merged[city][dist][ward].extend(
                                [s for s in streets if isinstance(s, str) and s.strip()]
                            )
                        elif isinstance(streets, str) and streets.strip():
                            merged[city][dist][ward].append(streets.strip())

        for city in merged:
            for dist in merged[city]:
                for ward, lst in merged[city][dist].items():
                    merged[city][dist][ward] = sorted(set(lst))

        return city_map_shape(merged)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get estimate cost
@app.post("/estimate_cost")
async def property_submit(p: PropertyIn):
    query = {
        "Thanh_pho": p.city,
        "Quan": p.district,
        "Phuong": p.ward,
        "Duong": p.street,
    }

    projection = {"Gia_ban": 1, "Dien_tich_dat": 1, "_id": 0}
    collection = app.state.db.baidangbds
    ket_qua_cursor = collection.find(query, projection)
    ket_qua = await ket_qua_cursor.to_list(length=None)

    # Calulate average price
    tong_don_gia = 0.0
    so_luong_hop_le = 0

    for doc in ket_qua:
        gia_ban = doc.get("Gia_ban")
        dien_tich = doc.get("Dien_tich_dat")

        if (
            isinstance(gia_ban, (int, float))
            and isinstance(dien_tich, (int, float))
            and dien_tich > 0
        ):
            if gia_ban > 100000 and dien_tich > 10:
                # Cộng dồn kết quả tính toán
                tong_don_gia += gia_ban / dien_tich
                # Tăng biến đếm
                so_luong_hop_le += 1

    trung_binh_cuoi_cung = 0
    try:
        if so_luong_hop_le > 0:
            trung_binh_cuoi_cung = tong_don_gia / so_luong_hop_le
        else:
            raise HTTPException(
                status_code=404, detail="No valid records found for the given criteria."
            )
    except ZeroDivisionError:
        raise HTTPException(status_code=500, detail="Error calculating average price.")

    return {"Don gia": trung_binh_cuoi_cung, "Gia": p.land_area * trung_binh_cuoi_cung}


# @app.get("/predict_chart")
# async def predict_chart():
#     try:
#         return {"msg": "This function will be develop soon."}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict")
async def predict(p: PropertyIn):
    try:
        # --- Lấy dữ liệu từ MongoDB ---
        collection = app.state.db.giatrungbinh
        docs = collection.find({}, {"_id": 0})

        data = {}
        async for doc in docs:
            for city, item in doc.items():
                if city == p.city:
                    for dist, item2 in item.items():
                        if dist == p.district:
                            for ward, item3 in item2.items():
                                if ward == p.ward:
                                    data[ward] = item3
                                    break

        if not data:
            raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu")

        # --- Chuyển dữ liệu thành DataFrame ---
        print("Chuyển dữ liệu thành DataFrame")
        df = pd.DataFrame(data).reset_index()
        df["Phuong"] = " " + p.ward
        df.columns = ["Time", "GiaTri", "Phuong"]
        df.Time = pd.to_datetime(df.Time)

        # --- Feature engineering ---
        print("Bắt đầu quá trình Feature Engineering")
        df["year"] = df["Time"].dt.year
        df["month"] = df["Time"].dt.month
        df["quarter"] = df["Time"].dt.quarter
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
        df["GiaTri_log"] = np.log1p(df["GiaTri"])

        df = df.sort_values(["Phuong", "Time"]).reset_index(drop=True)
        for lag in [1, 2, 3]:
            df[f"GiaTri_log_lag{lag}"] = df.groupby("Phuong")["GiaTri_log"].shift(lag)
        df["GiaTri_log_roll3"] = (
            df.groupby("Phuong")["GiaTri_log"].shift(1).rolling(window=3).mean()
        )
        df["GiaTri_log_roll6"] = (
            df.groupby("Phuong")["GiaTri_log"].shift(1).rolling(window=6).mean()
        )
        df = df.dropna().reset_index(drop=True)
        print("Feature Engineering completed")

        # --- Load encoder & scaler từ training ---
        print("Load Label encoding & Scaler")
        le = joblib.load(
            "/home/bang/Documents/QuinTech_AI_BDS_APP/Backend/model/label_encoder.pkl"
        )
        scaler = joblib.load(
            "/home/bang/Documents/QuinTech_AI_BDS_APP/Backend/model/scaler.pkl"
        )
        print("Label encoding & Scaler loaded successfully")

        # Đang lỗi chỗ này nè1
        df = df.sample(n=50, replace=True, random_state=42).reset_index(drop=True)

        features = scaler.feature_names_in_.tolist()
        phuong_col = "Phuong"
        seq_len = 24
        pred_len = 3

        # Encode phuong bằng encoder đã train
        df[phuong_col] = le.transform(df[phuong_col])

        # Chuẩn hóa features bằng scaler đã train
        df[features] = scaler.transform(df[features])
        print("Features scaled successfully")

        # --- Chuẩn bị input ---
        if len(df) < seq_len:
            print("Không đủ dữ liệu để dự báo")
            raise HTTPException(status_code=400, detail="Không đủ dữ liệu để dự báo")

        x = df.iloc[-seq_len:][features].values.astype("float32")
        phuong = df.iloc[-1][phuong_col]

        # --- Load model ---
        print("Load model")
        checkpoint = (
            "/home/bang/Documents/QuinTech_AI_BDS_APP/Backend/model/stockformer.pt"
        )
        model = Stockformer(
            num_features=len(features),
            num_phuong=len(le.classes_),  # phải khớp với lúc train
            d_model=128,
            nhead=4,
            num_layers=3,
            output_len=pred_len,
        )
        model.load_state_dict(torch.load(checkpoint, map_location="cpu"))
        model.eval()
        print("Model loaded successfully")

        # --- Dự báo ---
        print("Bắt đầu quá trình Dự báo")
        with torch.no_grad():
            xb = torch.tensor(x).unsqueeze(0)  # [1, seq_len, features]
            phuongb = torch.tensor([phuong])  # [1]
            preds = model(xb, phuongb)

        pred = np.expm1(preds.detach().cpu().numpy()).flatten().tolist()
        true = np.expm1(df["GiaTri"].to_numpy()).tolist()
        timeline = df.Time.dt.strftime("%Y-%m").tolist()

        # tạo mốc thời gian tương lai
        # last_time = pd.to_datetime(timeline[-1])
        # for i in range(pred_len):
        #     next_time = last_time + pd.DateOffset(months=i + 1)
        #     timeline.append(next_time.strftime("%Y-%m"))

        return {"predictions": pred, "true": true, "timeline": sorted(timeline)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
