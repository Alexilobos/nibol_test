# Prueba técnica — Andes Retail Analytics Group

Proyecto reproducible para simular ventas, construir un modelo analítico en SQL Server, automatizar procesos y desarrollar analítica predictiva y Power BI.

## Principios

- Datos sintéticos con lógica estadística, no aleatoriedad independiente.
- Código, configuración y decisiones versionados con Git.
- Datos generados fuera de Git: deben poder regenerarse con una semilla fija.
- Cada componente debe ser explicable durante la defensa técnica.

## Estructura

- `config/`: parámetros de ejecución.
- `data/`: datos generados.
- `docs/`: decisiones, arquitectura y documentación.
- `sql/`: modelo, procedimientos, jobs y alertas.
- `src/`: scripts Python.
- `tests/`: validaciones.
- `powerbi/`: instrucciones y archivo PBIX final.