import pandas as pd
import numpy as np
import os


def process_data(path):
    df = pd.read_csv(path)
    final = df[["Ma_BDS", "Ngay_dang", "So_phong_ngu", "So_nha_tam"]]

    arr = (
        df["Dia_chi"]
        .str.split(",")
        .apply(lambda x: x if len(x) == 4 else [x[0] + ", " + x[1], x[2], x[3], x[4]])
    )
    final["Duong"] = arr.apply(lambda x: x[0])
    final["Phuong"] = arr.apply(lambda x: x[1])
    final["Quan"] = arr.apply(lambda x: x[2])
    final["Thanh_pho"] = arr.apply(lambda x: x[3])

    final["Dien_tich_su_dung"] = (
        df["Dien_tich_su_dung"]
        .str.replace("m2", "")
        .str.strip()
        .str.replace(",", ".")
        .astype(float)
    )

    final["Dien_tich_dat"] = (
        df["Dien_tich_dat"]
        .str.split("m2")
        .str[0]
        .str.strip()
        .str.replace(",", ".")
        .astype(float)
    )

    daixrong = (
        df["Dien_tich_dat"]
        .str.split(" ")
        .str[-1]
        .str.replace("(", "")
        .str.replace(")", "")
        .str.replace(",", ".")
    )
    daixrong = daixrong.str.replace("m2", "0x0")
    final["Chieu_dai"] = daixrong.str.split("x").str[-1].astype(float)
    final["Chieu_rong"] = daixrong.str.split("x").str[0].astype(float)

    final["Gia_ban"] = (
        df["Gia_dat"]
        .str.replace(" tỷ", "000000000")
        .str.replace(" triệu", "000000")
        .str.replace(" nghìn", "000")
        .str.split(" ")
        .apply(lambda x: sum([int(i) for i in x if i.isdigit()]))
        .astype(float)
    )

    file_name = path.split("/")[-1]

    if not os.path.exists("/".join(path.split("/")[:-2]) + "/data_clear"):
        os.makedirs("/".join(path.split("/")[:-2]) + "/data_clear")

    final.to_csv(
        os.path.join("/".join(path.split("/")[:-2]) + "/data_clear/" + file_name),
        index=False,
    )


if __name__ == "__main__":
    folds = "data/quan-binh-thanh/data_info"
    files = os.listdir(folds)
    for file in files:
        process_data(os.path.join(folds, file))
    print("Data processing complete.")
