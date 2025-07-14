import json
from pathlib import Path
import optuna
import mlflow
from pairsplus.backtest import run_backtest

mlflow.set_experiment("PairsPlus-Hyperparameter-Tuning")


def objective(trial):
    params = {
        "z_threshold": trial.suggest_float("z_threshold", 0.5, 3.0),
        "lookback_days": trial.suggest_int("lookback_days", 30, 365),
        "rolling_window": trial.suggest_int("rolling_window", 10, 120),
        "kalman_cov": trial.suggest_float("kalman_cov", 1e-4, 1e-2),
    }

    score = run_backtest(**params)

    with mlflow.start_run():
        mlflow.log_params(params)
        mlflow.log_metric("score", score)

    return score


if __name__ == "__main__":
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=50)

    best_trial = study.best_trial

    print("\n" + "=" * 40)
    print("✅ BEST TRIAL RESULTS")
    print("=" * 40)
    print(f"⭐ Best Score: {best_trial.value:.2f}")
    print("🔎 Best Hyperparameters:")
    for k, v in best_trial.params.items():
        print(f"   - {k}: {v}")
    print("=" * 40 + "\n")

    # Log best trial to MLflow
    with mlflow.start_run(run_name="best_trial"):
        mlflow.log_params(best_trial.params)
        mlflow.log_metric("score", best_trial.value)

    # Save best hyperparameters to JSON file
    best_params_path = Path("best_hyperparams.json")
    with open(best_params_path, "w") as f:
        json.dump(best_trial.params, f, indent=2)

    print(f"\n✅ Best hyperparameters saved to {best_params_path.resolve()}\n")
