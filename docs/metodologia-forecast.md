# Metodología de forecast de ventas

## Objetivo

Proyectar ventas netas mensuales para los 12 meses posteriores al último dato disponible, con evaluación temporal y selección objetiva de modelo.

## Datos y granularidad

La fuente es `data/raw/fact_ventas.csv`, con 5.000 transacciones entre enero de 2023 y diciembre de 2025.

El modelo opera a nivel **región–categoría–mes**: 4 regiones por 6 categorías, equivalentes a 24 series mensuales.

No se modeló inicialmente a nivel sucursal–categoría porque 5.000 transacciones repartidas entre 120 sucursales, 6 categorías y 36 meses producen series demasiado dispersas. Esa granularidad dejó una proporción alta de combinaciones sin observaciones suficientes para validación. La agregación regional conserva la señal estacional y permite una comparación estadística más fiable.

## Validación temporal

Se utilizó una separación temporal, no aleatoria:

- Entrenamiento: primeros 30 meses.
- Validación: últimos 6 meses.
- Horizonte final: 12 meses de 2026.

Este enfoque evita fuga de información futura hacia el entrenamiento y representa el escenario operativo real de pronosticar meses aún no observados.

## Modelos comparados

1. **Baseline estacional**: repite el valor observado en el mismo mes del ciclo anual anterior.
2. **Holt-Winters aditivo con tendencia amortiguada**: modela nivel, tendencia y estacionalidad anual de 12 meses.

La métrica principal de selección fue MAE, porque se expresa en BOB y su interpretación es directa para negocio. También se calcula sMAPE como métrica porcentual complementaria.

## Resultado

Se evaluaron 24 series:

- Holt-Winters fue seleccionado en 22 series.
- El baseline estacional fue seleccionado en 2 series.
- MAE promedio baseline: 1.179,57 BOB.
- MAE promedio Holt-Winters: 940,42 BOB.
- Mejora aproximada: 20% en MAE promedio.

El modelo seleccionado se reentrena con los 36 meses disponibles antes de producir el horizonte 2026. Se generan 288 pronósticos: 24 series por 12 meses.

## Métodos no seleccionados

No se aplicó SARIMA/ARIMA como modelo principal porque cada serie tiene solo 36 observaciones mensuales, equivalentes a tres años y tres ciclos estacionales completos. Un modelo con varios parámetros autoregresivos y estacionales sería menos estable y tendría mayor riesgo de sobreajuste.

Tampoco se utilizó un modelo de machine learning como forecast principal: 36 observaciones por serie no ofrecen el volumen temporal necesario para entrenar y validar un modelo complejo de forma confiable. Las variables macroeconómicas pueden incorporarse después mediante escenarios o regresión dinámica cuando exista mayor historial.

## Reproducibilidad

```bash
python src/modelar_forecast.py