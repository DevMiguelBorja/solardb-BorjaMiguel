"""Punto de entrada unico del pipeline ETL de SolarDB.

Flujo: (simular) -> leer y validar JSONL -> staging -> lectura_demo -> etl_log.

Uso:
    python etl/run_etl.py              # simula solo si falta el archivo
    python etl/run_etl.py --simular    # regenera data/lecturas.jsonl

La conexion se toma de las variables de entorno estandar de PostgreSQL
(PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD), que se leen del archivo
.env (excluido del repositorio). Nunca se escriben credenciales en el codigo.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json, execute_values

import simulador

RAIZ = Path(__file__).resolve().parent.parent
SQL_DIR = RAIZ / "sql"
ARCHIVO = simulador.RUTA_SALIDA
PROCESO = "carga_lecturas_demo"


def leer_sql(nombre):
    return (SQL_DIR / nombre).read_text(encoding="utf-8")


def es_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def validar(msg):
    """True si el mensaje cumple tipos y rangos (los mismos de los CHECK)."""
    if not isinstance(msg, dict):
        return False
    device_id = msg.get("device_id")
    if not isinstance(device_id, int) or isinstance(device_id, bool):
        return False
    try:
        ts = datetime.fromisoformat(msg.get("ts"))
    except (TypeError, ValueError):
        return False
    if ts.tzinfo is None:
        return False
    p_ac, irr, temp = msg.get("p_ac"), msg.get("irradiancia"), msg.get("temp_modulo")
    if not (es_numero(p_ac) and es_numero(irr) and es_numero(temp)):
        return False
    return p_ac >= 0 and 0 <= irr <= 1500


def leer_archivo(ruta):
    """Devuelve (mensajes validos, filas leidas, filas rechazadas)."""
    validos, leidas, rechazadas = [], 0, 0
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            leidas += 1
            try:
                msg = json.loads(linea)
            except json.JSONDecodeError:
                rechazadas += 1
                continue
            if validar(msg):
                validos.append(msg)
            else:
                rechazadas += 1
    return validos, leidas, rechazadas


def cargar_staging(cur, mensajes):
    """Vacia el staging y carga el lote actual (una linea del archivo por fila)."""
    cur.execute("DELETE FROM stg_lectura_raw")
    execute_values(
        cur,
        "INSERT INTO stg_lectura_raw (payload) VALUES %s",
        [(Json(m),) for m in mensajes],
    )


def main():
    parser = argparse.ArgumentParser(description="Pipeline ETL de SolarDB")
    parser.add_argument("--simular", action="store_true",
                        help="regenera data/lecturas.jsonl antes de cargar")
    args = parser.parse_args()

    load_dotenv(RAIZ / ".env")

    if args.simular or not ARCHIVO.exists():
        n = simulador.simular(ARCHIVO)
        print(f"[simulador] {n} mensajes escritos en data/lecturas.jsonl")

    inicio = datetime.now(timezone.utc)
    try:
        conn = psycopg2.connect()  # usa las variables PG* del entorno
    except psycopg2.OperationalError as exc:
        print(f"No se pudo conectar a PostgreSQL: {exc}", file=sys.stderr)
        return 1

    # Las tablas se crean primero y en su propia transaccion: asi etl_log
    # existe aunque la carga falle.
    with conn, conn.cursor() as cur:
        cur.execute(leer_sql("01_tablas.sql"))

    leidas = cargadas = rechazadas = 0
    estado, error = "EXITO", None
    try:
        validos, leidas, rechazadas = leer_archivo(ARCHIVO)
        with conn, conn.cursor() as cur:  # una transaccion: todo o nada
            cargar_staging(cur, validos)
            cur.execute(leer_sql("02_carga.sql"))
            cargadas = cur.rowcount
        if rechazadas:
            estado = "PARCIAL"
    except Exception as exc:  # se registra en la bitacora y se informa
        estado, error = "ERROR", str(exc)
        cargadas = 0

    fin = datetime.now(timezone.utc)
    with conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO etl_log (proceso, archivo_origen, inicio, fin,
                   filas_leidas, filas_cargadas, filas_rechazadas, estado, error)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (PROCESO, ARCHIVO.relative_to(RAIZ).as_posix(), inicio, fin,
             leidas, cargadas, rechazadas, estado, error),
        )
    conn.close()

    omitidas = leidas - rechazadas - cargadas if estado != "ERROR" else 0
    print(f"[etl] estado={estado} leidas={leidas} cargadas={cargadas} "
          f"rechazadas={rechazadas} omitidas_por_duplicado={omitidas}")
    if error:
        print(f"[etl] error: {error}", file=sys.stderr)
    return 1 if estado == "ERROR" else 0


if __name__ == "__main__":
    sys.exit(main())
