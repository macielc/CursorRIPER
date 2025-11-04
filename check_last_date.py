import pandas as pd

print("Reading last lines of CSV...")
df = pd.read_csv('data/golden/WINFUT_M5_Golden_Data.csv')
print(f"Total rows in file: {len(df):,}")

print("\nLast 10 time values:")
print(df['time'].tail(10).values)

df['time'] = pd.to_datetime(df['time'])
print(f"\nDate range: {df['time'].min()} to {df['time'].max()}")

# Find days with good volume
print("\nFinding days with highest volume...")
df['date'] = df['time'].dt.date
daily_stats = df.groupby('date').agg({
    'real_volume': 'sum',
    'amplitude': 'mean'
}).sort_values('real_volume', ascending=False)

print("\nTop 10 days by volume:")
print(daily_stats.head(10))

