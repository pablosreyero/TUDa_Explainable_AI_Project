"""
smoke_run_model_search.py

Quick smoke-run that loads `data_new.csv`, takes a random subsample for speed,
runs grid_search_models with cv=2 (fast) and writes results to CSV files.

Intended for quick local validation only.
"""

import pandas as pd
from model_search import grid_search_models

# Load data
df = pd.read_csv('data_new.csv')
print('Loaded data_new.csv: rows={}, cols={}'.format(df.shape[0], df.shape[1]))

# Quick subsample for speed (adjust n or remove sampling for full runs)
n_sample = 500
if df.shape[0] > n_sample:
    df_s = df.sample(n=n_sample, random_state=0).reset_index(drop=True)
else:
    df_s = df.copy()

# Regression target
if 'cost_t' not in df_s.columns:
    raise RuntimeError("Expected column 'cost_t' in data_new.csv for regression smoke test")

y = df_s['cost_t']
X = df_s.select_dtypes(include=['number']).drop(columns=['cost_t'])

print('Running quick regression grid search on sample: X.shape={}, y.shape={}'.format(X.shape, y.shape))
res = grid_search_models(X, y, task='regression', cv=2, n_jobs=1, verbose=1)
res.to_csv('smoke_grid_search_reg_results.csv', index=False)
print('Saved smoke_grid_search_reg_results.csv')
print(res)
