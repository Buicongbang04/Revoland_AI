import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import LabelEncoder, StandardScaler
from landTransformer import Stockformer


def predict_future(
    data_path, seq_len, pred_len, feature_cols, target_col, phuong_col, checkpoint
):
    # Load data
    df = pd.read_csv(data_path)

    # Encode phuong
    le = LabelEncoder()
    df[phuong_col] = le.fit_transform(df[phuong_col])
    num_phuong = df[phuong_col].nunique()

    # Chuẩn hóa numeric features
    scaler = StandardScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])

    # Lấy seq_len gần nhất
    x = df.iloc[-seq_len:][feature_cols].values.astype("float32")
    phuong = df.iloc[-1][phuong_col]

    # Load model
    model = Stockformer(
        num_features=len(feature_cols),
        num_phuong=num_phuong,
        d_model=128,
        nhead=4,
        num_layers=3,
        output_len=pred_len,
    )
    model.load_state_dict(torch.load(checkpoint, map_location="cpu"))
    model.eval()

    # Dự báo
    with torch.no_grad():
        xb = torch.tensor(x).unsqueeze(0)  # [1, seq_len, F]
        phuongb = torch.tensor([phuong])
        preds = model(xb, phuongb)
    print("Dự báo", pred_len, "tháng tới:", np.expm1(preds).numpy())
    return np.expm1(preds.numpy())


if __name__ == "__main__":
    feature_cols = [
        "year",
        "month",
        "quarter",
        "month_sin",
        "month_cos",
        "GiaTri_log_lag1",
        "GiaTri_log_lag2",
        "GiaTri_log_lag3",
        "GiaTri_log_roll3",
        "GiaTri_log_roll6",
    ]
    predict_future(
        data_path="data.csv",
        seq_len=24,
        pred_len=3,
        feature_cols=feature_cols,
        target_col="GiaTri_log",
        phuong_col="Phuong",
        checkpoint="stockformer.pt",
    )
