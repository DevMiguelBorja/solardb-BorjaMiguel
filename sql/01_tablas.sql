-- Tablas de la practica (idempotente: se puede ejecutar varias veces).

CREATE TABLE IF NOT EXISTS stg_lectura_raw (
    id         BIGSERIAL PRIMARY KEY,
    payload    JSONB NOT NULL,
    cargado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lectura_demo (
    dispositivo_id INT NOT NULL,
    ts             TIMESTAMPTZ NOT NULL,
    p_ac           NUMERIC(10,3) CHECK (p_ac >= 0),
    irradiancia    NUMERIC(8,1) CHECK (irradiancia BETWEEN 0 AND 1500),
    temp_modulo    NUMERIC(5,1),
    payload        JSONB,
    PRIMARY KEY (dispositivo_id, ts)
);

-- Bitacora del proceso ETL (trazabilidad / data lineage)
CREATE TABLE IF NOT EXISTS etl_log (
    id               BIGSERIAL PRIMARY KEY,
    proceso          TEXT NOT NULL,
    archivo_origen   TEXT,
    inicio           TIMESTAMPTZ NOT NULL,
    fin              TIMESTAMPTZ,
    filas_leidas     INT,
    filas_cargadas   INT,
    filas_rechazadas INT,
    estado           TEXT NOT NULL CHECK (estado IN ('EXITO','ERROR','PARCIAL')),
    error            TEXT
);
