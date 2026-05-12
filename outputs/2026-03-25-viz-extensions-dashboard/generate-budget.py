"""
Generate budget data for WOW challenge based on Superstore actuals.
Budget = Actual * seasonal_factor * random_noise
Granularity: Region, Segment, Category, Sub-Category, YearMonth
"""
import pandas as pd
import numpy as np

np.random.seed(42)

df = pd.read_excel('../../common/Sample - Superstore.xls')
df['YearMonth'] = df['Order Date'].dt.to_period('M')

actual = df.groupby(['Region', 'Segment', 'Category', 'Sub-Category', 'YearMonth'])['Sales'].sum().reset_index()
actual.columns = ['Region', 'Segment', 'Category', 'Sub-Category', 'YearMonth', 'Actual_Sales']

# Seasonal adjustment by month (Q4 targets higher, Q1 lower)
seasonal = {
    1: 0.90, 2: 0.88, 3: 0.95, 4: 0.98, 5: 1.00, 6: 1.02,
    7: 0.97, 8: 0.96, 9: 1.05, 10: 1.08, 11: 1.15, 12: 1.20
}

rows = []
for _, row in actual.iterrows():
    month = row['YearMonth'].month
    base = row['Actual_Sales'] * seasonal[month]
    noise = np.random.uniform(0.90, 1.15)
    budget = round(base * noise, 2)

    rows.append({
        'Region': row['Region'],
        'Segment': row['Segment'],
        'Category': row['Category'],
        'Sub-Category': row['Sub-Category'],
        'YearMonth': str(row['YearMonth']),
        'Budget': budget
    })

budget_df = pd.DataFrame(rows)
budget_df.to_csv('budget.csv', index=False)
print(f'Saved {len(budget_df)} rows')
