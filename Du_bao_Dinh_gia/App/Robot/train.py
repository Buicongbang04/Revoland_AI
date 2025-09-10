import pandas as pd
import numpy as np
import joblib
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import r2_score
from landTransformer import Stockformer


# ---------------- Dataset ----------------
class HouseDataset(Dataset):
    def __init__(self, data, seq_len, pred_len, feature_cols, target_col, phuong_col):
        self.data = data.reset_index(drop=True)
        self.seq_len = seq_len
        self.pred_len = pred_len
        self.feature_cols = feature_cols
        self.target_col = target_col
        self.phuong_col = phuong_col

    def __len__(self):
        return len(self.data) - self.seq_len - self.pred_len

    def __getitem__(self, idx):
        x = self.data.iloc[idx : idx + self.seq_len][self.feature_cols].values.astype(
            np.float32
        )
        y = self.data.iloc[idx + self.seq_len : idx + self.seq_len + self.pred_len][
            self.target_col
        ].values.astype(np.float32)
        phuong = self.data.iloc[idx + self.seq_len - 1][self.phuong_col]
        return torch.tensor(x), torch.tensor(y), torch.tensor(phuong)


# ---------------- Training ----------------
def train_model(config):
    # Load data
    df = pd.read_csv(config["data_path"])

    # Encode phuong
    le = LabelEncoder()
    df["Phuong"] = le.fit_transform(df["Phuong"])
    num_phuong = df["Phuong"].nunique()

    # Chuẩn hóa numeric features
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
    scaler = StandardScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])

    # Dataset & split
    dataset = HouseDataset(
        df, config["seq_len"], config["pred_len"], feature_cols, "GiaTri_log", "Phuong"
    )
    train_size = int(len(dataset) * 0.8)
    test_size = len(dataset) - train_size
    train_set, test_set = torch.utils.data.random_split(  # type: ignore
        dataset, [train_size, test_size]
    )

    train_loader = DataLoader(train_set, batch_size=config["batch_size"], shuffle=True)
    test_loader = DataLoader(test_set, batch_size=config["batch_size"])

    # Model
    model = Stockformer(
        num_features=len(feature_cols),
        num_phuong=num_phuong,
        d_model=128,
        nhead=4,
        num_layers=3,
        output_len=config["pred_len"],
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Optimizer & Loss
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["lr"])
    criterion = nn.MSELoss()

    # Training loop
    for epoch in range(config["epochs"]):
        model.train()
        total_loss = 0
        for xb, yb, phuong in train_loader:
            xb, yb, phuong = xb.to(device), yb.to(device), phuong.to(device)
            optimizer.zero_grad()
            preds = model(xb, phuong)
            loss = criterion(preds, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for xb, yb, phuong in test_loader:
                xb, yb, phuong = xb.to(device), yb.to(device), phuong.to(device)
                preds = model(xb, phuong)
                loss = criterion(preds, yb)
                val_loss += loss.item()
        print(
            f"Epoch {epoch+1}/{config['epochs']} | Train Loss: {total_loss/len(train_loader):.4f} | Val Loss: {val_loss/len(test_loader):.4f}"
        )

    torch.save(model.state_dict(), "stockformer.pt")
    joblib.dump(le, "label_encoder.pkl")
    joblib.dump(scaler, "scaler.pkl")
    print("Training Finished: Model saved to stockformer.pt")


if __name__ == "__main__":
    config = {
        "data_path": "/home/bang/Documents/QuinTech_AI_BDS_APP/Robot/data.csv",
        "seq_len": 24,  # số tháng quá khứ dùng làm input
        "pred_len": 3,  # số tháng tương lai cần dự báo
        "batch_size": 32,
        "lr": 1e-3,
        "epochs": 1000,
    }
    train_model(config)
