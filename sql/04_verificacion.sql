-- Consultas para las capturas de los pasos 2, 4 y 5.
SELECT COUNT(*) AS filas_staging FROM stg_lectura_raw;
SELECT COUNT(*) AS filas_lectura_demo FROM lectura_demo;
SELECT dispositivo_id, COUNT(*) AS lecturas FROM lectura_demo GROUP BY dispositivo_id ORDER BY 1;
SELECT id, estado, filas_leidas, filas_cargadas, filas_rechazadas, inicio, fin FROM etl_log ORDER BY id;
