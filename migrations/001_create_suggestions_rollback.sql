-- Rollback de la migración 001. Elimina SOLO la tabla `suggestions`
-- (y con ella las sugerencias guardadas). No afecta otras tablas.
DROP TABLE IF EXISTS suggestions;
