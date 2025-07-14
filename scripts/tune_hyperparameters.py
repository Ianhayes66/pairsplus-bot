#!/usr/bin/env python

import argparse
import json
from pathlib import Path
import optuna
import mlflow
from pairsplus.backtest import run_backtest

MLFLOW_EXPERIMENT = "PairsPlus-Hyperparameter-Tuning"
BEST_PARAMS_FILE = Path("best_hyperparams.json")


def objective(trial, enable_mlflow=True):
    params = {
        "z_threshold": trial.suggest_float("z_threshold", 0.5, 3.0),
        "lookback_days": trial.suggest_int("lookback_days", 30, 365),
        "rolling_window": trial.suggest_int("rolling_window", 10, 120),
        "kalman_cov": trial.suggest_float("kalman_cov", 1e-4, 1e-2),
    }

    score = run_backtest(**params)

    if enable_mlflow:
        with mlflow.start_run():
            mlflow.log_params(params)
            mlflow.log_metric("score", score)

    return score


def main():
    parser = argparse.ArgumentParser(
        description="Hyperparameter tuning for PairsPlus."
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=50,
        help="Number of Optuna trials to run (default: 50)"
    )
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        help="Disable MLflow logging"
    )
    args = parser.parse_args()

    enable_mlflow = not args.no_mlflow

    if enable_mlflow:
        mlflow.set_experiment(MLFLOW_EXPERIMENT)

    print(f"\n🚀 Starting hyperparameter tuning with {args.trials} trials...\n")
    study = optuna.create_study(direction="maximize")
    study.optimize(lambda trial: objective(trial, enable_mlflow), n_trials=args.trials)

    best_trial = study.best_trial

    print("\n" + "=" * 50)
    print("✅ BEST TRIAL RESULTS")
    print("=" * 50)
    print(f"⭐ Best Score: {best_trial.value:.2f}")
    print("🔎 Best Hyperparameters:")
    for k, v in best_trial.params.items():
        print(f"   - {k}: {v}")
    print("=" * 50 + "\n")

    # Save best hyperparameters to JSON
    with open(BEST_PARAMS_FILE, "w") as f:
        json.dump(best_trial.params, f, indent=2)

    print(f"✅ Best hyperparameters saved to: {BEST_PARAMS_FILE.resolve()}")

    # Log best trial separately to MLflow
    if enable_mlflow:
        with mlflow.start_run(run_name="best_trial"):
            mlflow.log_params(best_trial.params)
            mlflow.log_metric("score", best_trial.value)
        print("✅ Best trial also logged to MLflow.")


if __name__ == "__main__":
    main()