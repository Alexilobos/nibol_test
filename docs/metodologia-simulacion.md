# Metodología de simulación estadística

## Decisión

Los datos no se generarán con variables independientes ni con `RAND()` sin lógica.
Se utilizará un proceso generativo condicionado por calendario, sucursal, cliente,
producto y contexto económico.

## Componentes del proceso

1. Calendario: 36 meses de ventas, con tendencia y estacionalidad anual.
2. Sucursales: 120 sucursales distribuidas en 4 regiones, cada una con un factor
   de demanda propio.
3. Variables macroeconómicas: inflación, dólar paralelo e índice macroeconómico
   evolucionan en el tiempo y afectan costo, precio y demanda.
4. Clima y tráfico: el clima depende de la región y afecta el tráfico; el tráfico
   influye positivamente en la cantidad vendida.
5. Clientes: cada cliente posee riesgo, lealtad y preferencia digital latentes.
   Esos factores afectan método de pago, satisfacción y probabilidad de fuga.
6. Productos: categoría, costo base, margen objetivo, popularidad e indicador de
   importación determinan precio y sensibilidad al dólar.
7. Cantidad: se usa distribución binomial negativa, no normal, porque es un
   conteo positivo con sobredispersión; su varianza puede ser mayor que su media.
8. Ruido: se incorpora ruido gaussiano moderado en precio, tráfico, entrega y
   satisfacción para no producir relaciones deterministas irreales.
9. Outliers: 2% de transacciones tienen cantidad o descuento extremo y quedan
   etiquetadas para poder analizarlas.

## Alternativas descartadas

- `RAND()`/uniforme independiente: no conserva correlaciones de negocio.
- Distribución normal para cantidad: puede producir valores negativos y no
  representa correctamente conteos.
- Poisson simple: asume media y varianza similares; ventas reales normalmente
  presentan sobredispersión.
- Modelo predictivo complejo desde el inicio: primero se construyen baselines
  interpretables y se comparan con métricas.