import pandas as pd

print("Checking Golden Data...")
df = pd.read_csv('data/golden/WINFUT_M5_Golden_Data.csv')
print(f"Total rows: {len(df):,}")

print("\nFirst 5 time values:")
print(df['time'].head())

print("\nConverting to datetime...")
df['time'] = pd.to_datetime(df['time'])

print(f"\nDate range: {df['time'].min()} to {df['time'].max()}")

print("\nChecking 2024-08-05...")
df_target = df[(df['time'].dt.year == 2024) & (df['time'].dt.month == 8) & (df['time'].dt.day == 5)]
print(f"Candles on 2024-08-05: {len(df_target)}")

if len(df_target) > 0:
    print("\nFirst 10 candles:")
    print(df_target[['time', 'open', 'high', 'low', 'close', 'real_volume']].head(10))
else:
    print("\nNo data for 2024-08-05!")
    print("\nLet's check what dates exist in August 2024:")
    df_aug = df[(df['time'].dt.year == 2024) & (df['time'].dt.month == 8)]
    if len(df_aug) > 0:
        dates_in_aug = df_aug['time'].dt.date.unique()
        print(f"Found {len(dates_in_aug)} unique dates in August 2024:")
        print(sorted(dates_in_aug)[:10])

