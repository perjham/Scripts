psql -qXtc "select datname from pg_catalog.pg_database where datname<>'template0'" template1
