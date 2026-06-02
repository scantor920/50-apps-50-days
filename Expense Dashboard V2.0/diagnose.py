import pandas as pd

cols = ['Vendor','Account Code','Department_Reporting','Function','Org_Level_1','Org_Level_2','Date Label','Actuals.Value','Budget.Value','PriorYear.Amount']
df = pd.read_csv('Expense Dashboard Data.csv', usecols=cols, low_memory=False)

for c in ['Actuals.Value','Budget.Value','PriorYear.Amount']:
    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

act = df[df['Actuals.Value'] != 0]

# For a single account + date, how many rows exist?
grp = act.groupby(['Account Code','Date Label'])['Actuals.Value']
cnt = grp.count().reset_index()
print('Max rows per Account+Date:', cnt['Actuals.Value'].max())
print('Mean rows per Account+Date:', cnt['Actuals.Value'].mean().round(1))

# Show example: one account in one period
example = act[(act['Account Code'] == '5615') & (act['Date Label'] == 'Mar-26')]
print('\n5615 + Mar-26:', len(example), 'rows, Actuals sum =', f"{example['Actuals.Value'].sum():,.0f}")
print(example[['Vendor','Department_Reporting','Function','Org_Level_1','Org_Level_2','Actuals.Value']].head(10).to_string())

# Q1 2026 check: sum only when grouped to unique account+date rows
q1 = act[act['Date Label'].isin(['Jan-26','Feb-26','Mar-26'])]
q1_total = q1['Actuals.Value'].sum()
print(f'\nQ1 2026 raw sum (all rows): {q1_total:,.0f}')

# If duplicate rows exist, deduplicate to unique account+dept+date
q1_dedup = q1.drop_duplicates(subset=['Account Code','Date Label','Department_Reporting','Org_Level_1','Org_Level_2'])
print(f'Q1 2026 deduped (acct+dept+period): {q1_dedup["Actuals.Value"].sum():,.0f} ({len(q1_dedup)} rows from {len(q1)} total)')

# Show distinct dimensions per account
dims = q1[q1['Account Code'] == '5615'].groupby(['Account Code','Date Label','Department_Reporting']).agg(
    rows=('Actuals.Value','count'),
    actuals_sum=('Actuals.Value','sum'),
    actuals_unique=('Actuals.Value','nunique')
).reset_index()
print('\n5615 Q1 rows grouped by Dept:')
print(dims.to_string())
