#!/usr/bin/env python3
"""DC Grocery Store Locations を出題用スキーマに変換する。

入力 (DC Open Data / Kaggle 由来):
    Grocery_Store_Locations.csv
    主な列: X, Y (Web Mercator EPSG:3857 メートル), STORENAME, ADDRESS,
            ZIPCODE, OBJECTID ...

出力スキーマ:
    Object ID, Address, Storename, Latitude, Longitude, Zipcode

X,Y は緯度経度ではなく Web Mercator (EPSG:3857) のメートル値なので、
球面メルカトルの逆変換で WGS84 緯度経度に変換する。
"""
import csv
import math
import sys

R = 6378137.0  # EPSG:3857 の地球半径(m)


def mercator_to_latlon(x, y):
    """Web Mercator (EPSG:3857) メートル -> WGS84 (lat, lon) 度"""
    lon = x / R * 180.0 / math.pi
    lat = (2.0 * math.atan(math.exp(y / R)) - math.pi / 2.0) * 180.0 / math.pi
    return lat, lon


def clean_zip(value):
    """'20001' / '20001.0' / '20001-1234' を 5桁文字列に正規化。空は ''。"""
    v = (value or "").strip()
    if not v:
        return ""
    v = v.split("-")[0]          # ZIP+4 -> 5桁
    if v.endswith(".0"):         # 数値読み込み由来の '.0' を除去
        v = v[:-2]
    return v


def convert(src_path, out_path):
    rows_out = []
    with open(src_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                x = float(row["X"])
                y = float(row["Y"])
            except (KeyError, ValueError):
                continue  # 座標が無い行はスキップ
            lat, lon = mercator_to_latlon(x, y)
            rows_out.append({
                "Object ID": (row.get("OBJECTID") or "").strip(),
                "Address": (row.get("ADDRESS") or "").strip(),
                "Storename": (row.get("STORENAME") or "").strip(),
                "Latitude": round(lat, 6),
                "Longitude": round(lon, 6),
                "Zipcode": clean_zip(row.get("ZIPCODE")),
            })

    fieldnames = ["Object ID", "Address", "Storename",
                  "Latitude", "Longitude", "Zipcode"]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)
    return len(rows_out)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "../Dataset/Grocery_Store_Locations.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "dc-grocery-clean.csv"
    n = convert(src, out)
    print(f"converted {n} rows -> {out}")
