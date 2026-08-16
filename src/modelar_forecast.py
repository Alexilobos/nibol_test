from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "raw" / "fact_ventas.csv"
OUTPUT_DIR = ROOT / "data" / "processed"

HORIZON = 12
VALIDATION_MONTHS = 6
SEASONAL_PERIODS = 12


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def smape(actual: np.ndarray, predicted: np.ndarray) -> float:
    denominator = np.abs(actual) + np.abs(predicted)
    valid = denominator > 0

    if not valid.any():
        return 0.0

    return float(
        100 * np.mean(
            2 * np.abs(actual[valid] - predicted[valid]) / denominator[valid]
        )
    )


def forecast_seasonal_naive(history: pd.Series, steps: int) -> np.ndarray:
    if len(history) < SEASONAL_PERIODS:
        raise ValueError("La serie no tiene 12 meses para baseline estacional.")

    return np.resize(history.iloc[-SEASONAL_PERIODS:].to_numpy(), steps)


def fit_holt_winters(history: pd.Series, steps: int) -> np.ndarray:
    model = ExponentialSmoothing(
        history,
        trend="add",
        damped_trend=True,
        seasonal="add",
        seasonal_periods=SEASONAL_PERIODS,
        initialization_method="estimated",
    )

    fitted = model.fit(optimized=True)
    return np.asarray(fitted.forecast(steps))


def build_monthly_series(ventas: pd.DataFrame) -> pd.DataFrame:
    ventas = ventas.copy()
    ventas["fecha"] = pd.to_datetime(ventas["fecha"])
    ventas["mes"] = ventas["fecha"].dt.to_period("M").dt.to_timestamp()

    grouped = (
        ventas.groupby(["region", "categoria", "mes"], as_index=False)["ingreso_neto"]
        .sum()
        .rename(columns={"ingreso_neto": "ventas_reales"})
    )

    full_months = pd.date_range(
        grouped["mes"].min(),
        grouped["mes"].max(),
        freq="MS",
    )

    completed = []

    for (region, categoria), group in grouped.groupby(["region", "categoria"]):
        series = (
            group.set_index("mes")["ventas_reales"]
            .reindex(full_months, fill_value=0.0)
            .rename_axis("mes")
            .reset_index()
        )
        series["region"] = region
        series["categoria"] = categoria
        completed.append(series)

    return pd.concat(completed, ignore_index=True)[
        ["region", "categoria", "mes", "ventas_reales"]
    ]


def evaluate_and_forecast(monthly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    comparison_rows = []
    forecast_rows = []

    for (region, categoria), group in monthly.groupby(["region", "categoria"]):
        series = (
            group.sort_values("mes")
            .set_index("mes")["ventas_reales"]
            .asfreq("MS", fill_value=0.0)
        )

        if len(series) <= VALIDATION_MONTHS + SEASONAL_PERIODS:
            raise ValueError(
                f"Serie insuficiente para {region} - {categoria}: {len(series)} meses."
            )

        train = series.iloc[:-VALIDATION_MONTHS]
        actual = series.iloc[-VALIDATION_MONTHS:].to_numpy()

        candidates = {
            "BASELINE_ESTACIONAL": forecast_seasonal_naive(
                train,
                VALIDATION_MONTHS,
            )
        }

        try:
            candidates["HOLT_WINTERS_ADITIVO"] = fit_holt_winters(
                train,
                VALIDATION_MONTHS,
            )
        except (ValueError, np.linalg.LinAlgError) as error:
            print(f"Holt-Winters omitido para {region} - {categoria}: {error}")

        candidate_metrics = {}

        for model_name, prediction in candidates.items():
            prediction = np.clip(prediction, 0, None)

            candidate_metrics[model_name] = {
                "mae": mae(actual, prediction),
                "smape": smape(actual, prediction),
            }

        selected_model = min(
            candidate_metrics,
            key=lambda name: candidate_metrics[name]["mae"],
        )

        for model_name, metrics in candidate_metrics.items():
            comparison_rows.append(
                {
                    "region": region,
                    "categoria": categoria,
                    "modelo": model_name,
                    "mae_validacion": round(metrics["mae"], 4),
                    "smape_validacion": round(metrics["smape"], 4),
                    "seleccionado": model_name == selected_model,
                }
            )

        if selected_model == "HOLT_WINTERS_ADITIVO":
            future = fit_holt_winters(series, HORIZON)
        else:
            future = forecast_seasonal_naive(series, HORIZON)

        future_dates = pd.date_range(
            series.index.max() + pd.offsets.MonthBegin(1),
            periods=HORIZON,
            freq="MS",
        )

        selected_metrics = candidate_metrics[selected_model]

        for date, prediction in zip(future_dates, np.clip(future, 0, None)):
            forecast_rows.append(
                {
                    "fecha": date.date().isoformat(),
                    "region": region,
                    "categoria": categoria,
                    "modelo_seleccionado": selected_model,
                    "ventas_proyectadas": round(float(prediction), 2),
                    "mae_validacion": round(selected_metrics["mae"], 4),
                    "smape_validacion": round(selected_metrics["smape"], 4),
                }
            )

    return pd.DataFrame(comparison_rows), pd.DataFrame(forecast_rows)


def main() -> None:
    required_columns = {"fecha", "region", "categoria", "ingreso_neto"}

    ventas = pd.read_csv(INPUT_PATH)

    missing_columns = required_columns.difference(ventas.columns)
    if missing_columns:
        raise ValueError(f"Columnas faltantes: {sorted(missing_columns)}")

    monthly = build_monthly_series(ventas)

    comparison, forecast = evaluate_and_forecast(monthly)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    comparison_path = OUTPUT_DIR / "comparacion_modelos_forecast.csv"
    forecast_path = OUTPUT_DIR / "forecast_region_categoria_2026.csv"

    comparison.to_csv(comparison_path, index=False)
    forecast.to_csv(forecast_path, index=False)

    print("Series evaluadas:", monthly.groupby(["region", "categoria"]).ngroups)
    print("\nModelos seleccionados:")
    print(forecast["modelo_seleccionado"].value_counts())
    print("\nMAE promedio por modelo:")
    print(comparison.groupby("modelo")["mae_validacion"].mean().round(2))
    print("\nPronósticos generados:", len(forecast))
    print(f"Comparación: {comparison_path}")
    print(f"Forecast: {forecast_path}")


if __name__ == "__main__":
    main()