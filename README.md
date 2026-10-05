# SolarDB Pascual · Pipeline de ingesta IoT

**Integrantes:** Miguel Borja 
**Curso:** Bases de Datos I (SD1006) · **Grupo:** 811 · **Semestre:** 2026-II
**Docente:** Ramiro Grisales Montoya

> An idempotent ETL pipeline that loads simulated IoT telemetry into a governed PostgreSQL repository, versioned on GitHub.

## Descripción del trabajo

Consulta en parejas sobre gobernanza de datos, automatización ETL e IoT aplicada a SolarDB. Incluye una práctica guiada: un simulador genera mensajes JSON de dos inversores, un pipeline los carga en PostgreSQL con un flujo idempotente (staging → tabla relacional) y un rol de solo lectura demuestra el mínimo privilegio. El informe completo está en `docs/`.

## Estructura

```
├── README.md
├── .gitignore
├── .env.example       plantilla de conexión (el .env real NO se sube)
├── requirements.txt
├── docs/              PDF de la consulta
├── data/              lecturas.jsonl de muestra
├── etl/
│   ├── simulador.py   genera los mensajes JSON de dos dispositivos
│   └── run_etl.py     punto de entrada único del pipeline
└── sql/
    ├── 01_tablas.sql  staging, lectura_demo y etl_log
    ├── 02_carga.sql   INSERT ... SELECT ... ON CONFLICT DO NOTHING
    ├── 03_roles.sql   rol solar_lector (solo lectura)
    └── 04_verificacion.sql  consultas para las capturas
```

## Cómo reproducir la práctica

Requisitos: Python 3.10 o superior y PostgreSQL 15 o superior.

1. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```
2. Crear la base de datos:
   ```
   psql -U postgres -c "CREATE DATABASE solardb;"
   ```
3. Copiar `.env.example` a `.env` y escribir allí los datos de conexión reales. El `.env` está en `.gitignore`.
4. Ejecutar el pipeline completo con un solo comando:
   ```
   python etl/run_etl.py
   ```
   Si falta `data/lecturas.jsonl`, lo genera el simulador. Para regenerarlo: `python etl/run_etl.py --simular`.
5. Prueba de idempotencia: ejecutar el comando una segunda vez y comparar el conteo con `sql/04_verificacion.sql`:
   ```
   psql -U postgres -d solardb -f sql/04_verificacion.sql
   ```
   El conteo de `lectura_demo` no cambia (288 filas con dos dispositivos y 144 lecturas cada uno). Cada ejecución queda registrada en `etl_log`.
6. Crear el rol de solo lectura y asignarle contraseña desde psql (nunca en el script):
   ```
   psql -U postgres -d solardb -f sql/03_roles.sql
   psql -U postgres -d solardb
   \password solar_lector
   ```
7. Probar el rol:
   ```
   psql -U solar_lector -d solardb -c "SELECT COUNT(*) FROM lectura_demo;"
   psql -U solar_lector -d solardb -c "INSERT INTO lectura_demo (dispositivo_id, ts, p_ac) VALUES (99, now(), 1);"
   ```
   El `SELECT` funciona y el `INSERT` es rechazado con `permission denied`.

## Programación cada hora (sin implementar)

cron (Linux/macOS):

```
0 * * * * cd /ruta/solardb-apellido1-apellido2 && python etl/run_etl.py
```

Programador de tareas de Windows: desencadenador diario repetido cada 1 hora, acción `python etl\run_etl.py` con la carpeta del repositorio como directorio de inicio.

## Decisiones de diseño

- **Carga a staging con psycopg2** (no `\copy`): corre dentro del mismo script, evita las reglas de escape de `\copy` con JSON y permite un único comando de punta a punta.
- **Staging por lote:** cada ejecución vacía `stg_lectura_raw` y carga el archivo actual. La idempotencia la garantiza la clave primaria `(dispositivo_id, ts)` de `lectura_demo`.
- **Validación previa:** las líneas con JSON inválido, tipos incorrectos o valores fuera de rango se rechazan y se cuentan en `filas_rechazadas`; el estado queda `PARCIAL`.
- **Todo o nada:** la carga a staging y a `lectura_demo` van en una sola transacción. Si falla, se hace rollback y `etl_log` registra el estado `ERROR`.
- **Sin credenciales en el código:** la conexión usa las variables de entorno `PG*` leídas del `.env`.

## Quién hizo qué

| Integrante | Aportes |
|---|---|
| [Nombre 1] | [Ej.: simulador, tablas, Parte A bloques 1 y 4] |
| [Nombre 2] | [Ej.: carga, bitácora, roles, Parte A bloques 2 y 3] |
