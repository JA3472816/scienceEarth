import pandas as pd
import os

def classify_by_year_and_monthly_avg(input_file):
    print(f"\n正在讀取檔案: {input_file} ...")
    # 從檔名取得前綴 (例如: bio_monthly.txt -> bio)
    prefix = os.path.basename(input_file).split('_')[0]
    
    # 讀取 txt 檔案 (假設為 tab 分隔)
    try:
        df = pd.read_csv(input_file, sep='\t')
    except Exception as e:
        print(f"讀取檔案失敗: {e}")
        return

    # 檢查是否有 'time' 欄位
    if 'time' not in df.columns:
        print("錯誤: 檔案中找不到 'time' 欄位！")
        return

    # 將 time 轉換為 datetime 物件，並提取年份與月份
    df['time'] = pd.to_datetime(df['time'])
    df['year'] = df['time'].dt.year
    df['month'] = df['time'].dt.month

    print("計算月平均值...")
    # 根據年份、月份以及空間座標(如 depth, latitude, longitude)分組取平均
    # 這樣可以確保每個月每個座標點只有一個平均值
    group_cols = ['year', 'month']
    for col in ['depth', 'latitude', 'longitude']:
        if col in df.columns:
            group_cols.append(col)
            
    # 計算平均值 (這會忽略非數值欄位，並將其餘如 nppv, o2 等變數取平均)
    df_monthly_avg = df.groupby(group_cols, as_index=False).mean()

    # 建立用來存放分類後檔案的資料夾
    output_dir = 'classified_by_year'
    os.makedirs(output_dir, exist_ok=True)

    # 根據 'year' 欄位進行群組分類
    grouped = df_monthly_avg.groupby('year')
    
    print(f"共找到 {len(grouped)} 個不同的年份。開始分類並儲存...")
    
    # 迭代每個年份的群組，並將其存成獨立的檔案
    for year_val, group in grouped:
        output_filename = os.path.join(output_dir, f"{prefix}_{year_val}.txt")
        
        # 移除我們輔助用的 year 欄位 (可選)
        group = group.drop(columns=['year'])
        
        # 將該群組的資料輸出成新的 txt 檔
        group.to_csv(output_filename, sep='\t', index=False)
        print(f" - 已儲存: {output_filename} (共 {len(group)} 筆資料)")

    print("分類完成！所有檔案已儲存至 'classified_by_year' 資料夾中。")

if __name__ == "__main__":
    files_to_process = ['bio_monthly.txt', 'pft_monthly.txt', 'nut_monthly.txt']
    for file_path in files_to_process:
        if os.path.exists(file_path):
            classify_by_year_and_monthly_avg(file_path)
        else:
            print(f"找不到檔案: {file_path}")
