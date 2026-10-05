"""Simulador IoT de SolarDB.

Genera mensajes JSON (uno por linea) de dos inversores, una lectura
cada 5 minutos durante 12 horas. Campo agregado respecto al script base:
"estado" (RUN o STANDBY, segun la potencia entregada).
"""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

TZ = timezone(timedelta(hours=-5))  # hora de Colombia
RAIZ = Path(__file__).resolve().parent.parent
RUTA_SALIDA = RAIZ / "data" / "lecturas.jsonl"
DISPOSITIVOS = [1, 2]
LECTURAS = 144  # 12 h, una lectura cada 5 min


def simular(ruta=RUTA_SALIDA):
    """Escribe el archivo JSONL y devuelve el numero de mensajes generados."""
    inicio = datetime(2026, 10, 5, 6, 0, tzinfo=TZ)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with open(ruta, "w", encoding="utf-8") as f:
        for i in range(LECTURAS):
            ts = (inicio + timedelta(minutes=5 * i)).isoformat()
            for device_id in DISPOSITIVOS:
                p_ac = round(random.uniform(0, 5.0), 3)  # kW
                msg = {
                    "device_id": device_id,
                    "ts": ts,
                    "p_ac": p_ac,
                    "irradiancia": round(random.uniform(0, 1000), 1),  # W/m2
                    "temp_modulo": round(random.uniform(18, 60), 1),  # grados C
                    "estado": "RUN" if p_ac > 0.1 else "STANDBY",
                }
                if random.random() < 0.03:
                    msg["alarma"] = "GRID_FAULT"
                f.write(json.dumps(msg) + "\n")
                total += 1
    return total


if __name__ == "__main__":
    n = simular()
    print(f"{n} mensajes escritos en {RUTA_SALIDA}")
