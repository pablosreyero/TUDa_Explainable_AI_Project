"""
model_search.py

Utility to run grid-searches over common regression and classification models
and return a summary DataFrame with best params and CV scores.

Usage (from a notebook):

from model_search import grid_search_models, default_models_params
res = grid_search_models(X, y, task='regression', cv=5, n_jobs=-1)
print(res)

To change parameter grids, either pass `models_params` with the same dict shape
or modify the default grid returned by `default_models_params(task)`.
"""

from typing import Dict, Tuple, Any
import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV, KFold, StratifiedKFold

# Models
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from xgboost import XGBRegressor, XGBClassifier


def default_models_params(task: str = "regression") -> Tuple[Dict[str, Tuple[Any, Dict[str, list]]], str]:
    """Return a dict of {name: (estimator, param_grid)} and a default scoring.

    task: 'regression' or 'classification'
    """
    # Use XGBoost models as defaults (small grids for quick experimentation)
    if task == "regression":
        models = {
            "XGBRegressor": (
                XGBRegressor(random_state=0, verbosity=0),
                {
                    "n_estimators": [50, 100],
                    "max_depth": [3, 5],
                    "learning_rate": [0.1, 0.01],
                    "subsample": [0.8, 1.0],
                },
            ),
            "RandomForestRegressor": (
                RandomForestRegressor(random_state=0),
                {"n_estimators": [50, 100], "max_depth": [None, 5, 10]},
            ),
        }
        scoring = "neg_mean_squared_error"
    else:
        models = {
            "XGBClassifier": (
                XGBClassifier(random_state=0, use_label_encoder=False, verbosity=0),
                {
                    "n_estimators": [50, 100],
                    "max_depth": [3, 5],
                    "learning_rate": [0.1, 0.01],
                    "subsample": [0.8, 1.0],
                    # 'eval_metric' can be set but GridSearchCV will not pass dataset for early stopping here
                },
            ),
            "RandomForestClassifier": (
                RandomForestClassifier(random_state=0),
                {"n_estimators": [50, 100], "max_depth": [None, 5, 10]},
            ),
        }
        scoring = "accuracy"

    return models, scoring


def grid_search_models(
    X,
    y,
    task: str = "regression",
    models_params: Dict[str, Tuple[Any, Dict[str, list]]] = None,
    cv: int = 5,
    scoring: str = None,
    n_jobs: int = 1,
    verbose: int = 0,
):
    """Run GridSearchCV for each model and return a pandas DataFrame with results.

    Parameters:
    - X, y: arrays or DataFrame/Series
    - task: 'regression' | 'classification'
    - models_params: optional dict mapping name -> (estimator, param_grid). If None, uses defaults.
    - cv: int folds
    - scoring: scoring string passed to GridSearchCV. If None, uses defaults from `default_models_params`.
    - n_jobs: parallel jobs
    - verbose: verbosity for GridSearchCV

    Returns:
    - pd.DataFrame with columns: ['model', 'best_score', 'best_params', 'estimator']
      Sorted by best_score (descending for classification, ascending for regression if using neg MSE).
    """
    if models_params is None:
        models_params, default_scoring = default_models_params(task)
        if scoring is None:
            scoring = default_scoring
    else:
        if scoring is None:
            # fallback scoring
            scoring = "accuracy" if task == "classification" else "neg_mean_squared_error"

    # CV strategy
    if task == "classification":
        cv_strategy = StratifiedKFold(n_splits=cv, shuffle=True, random_state=0)
    else:
        cv_strategy = KFold(n_splits=cv, shuffle=True, random_state=0)

    results = []

    for name, (estimator, param_grid) in models_params.items():
        print(f"Running GridSearch for: {name}")
        gs = GridSearchCV(
            estimator, param_grid, scoring=scoring, cv=cv_strategy, n_jobs=n_jobs, verbose=verbose
        )
        # Fit
        gs.fit(X, y) # training the model

        best_score = gs.best_score_
        best_params = gs.best_params_
        best_est = gs.best_estimator_

        results.append(
            {
                "model": name,
                "best_score": best_score,
                "best_params": best_params,
                "estimator": best_est,
            }
        )

    df_res = pd.DataFrame(results)
    # Sorting: higher is better for classification accuracy; for neg_mse (regression) higher (=less negative) is better too
    df_res = df_res.sort_values("best_score", ascending=False).reset_index(drop=True)
    return df_res


if __name__ == "__main__":
    # Small example: uses data_new.csv and expects you to set a y column name before running.
    import argparse

    parser = argparse.ArgumentParser(description="Run simple grid search on CSV dataset")
    parser.add_argument("--csv", default="data_new.csv", help="Path to CSV file (default: data_new.csv)")
    parser.add_argument("--ycol", default="cost_t", help="Target column name in CSV (default: cost_t)")
    parser.add_argument("--task", default="regression", choices=["regression", "classification"], help="Task type")
    parser.add_argument("--cv", type=int, default=3, help="Number of CV folds (default:3)")
    parser.add_argument("--n_jobs", type=int, default=1, help="Jobs for GridSearch (default:1)")

    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    if args.ycol not in df.columns:
        raise ValueError(f"y column '{args.ycol}' not found in {args.csv}. Columns: {df.columns.tolist()}")

    y = df[args.ycol]
    # Simple automatic feature selection: keep numeric predictors and drop the target
    X = df.select_dtypes(include=["number"]).drop(columns=[args.ycol])

    print(f"Running grid search: task={args.task}, X.shape={X.shape}, y.shape={y.shape}")
    res = grid_search_models(X, y, task=args.task, cv=args.cv, n_jobs=args.n_jobs)
    print(res.to_string())
