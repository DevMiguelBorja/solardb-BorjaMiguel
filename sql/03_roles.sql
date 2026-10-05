-- Rol de solo lectura (minimo privilegio). Ejecutar como administrador:
--   psql -U postgres -d solardb -f sql/03_roles.sql
-- La contrasena NO va aqui. Asignarla despues, dentro de psql:
--   \password solar_lector
-- Si la base no se llama solardb, cambiar el nombre en el GRANT CONNECT.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'solar_lector') THEN
        CREATE ROLE solar_lector LOGIN;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE solardb TO solar_lector;
GRANT USAGE ON SCHEMA public TO solar_lector;
GRANT SELECT ON lectura_demo TO solar_lector;
