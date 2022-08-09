#!/bin/bash
#su - postgres -c "pg_dumpall -U postgres > /tmp/entire.sql"

cat << EOF > /tmp/list_postgres_db.sh
psql -qXtc "select datname from pg_catalog.pg_database where datname<>'template0'" template1
EOF
mkdir /tmp/backup_postgres
rm -rf /tmp/backup_postgres/*
chown postgres /tmp/backup_postgres
for dbname in `su - postgres -c "sh /tmp/list_postgres_db.sh"`
do
  echo $dbname
  su - postgres -c "pg_dump -U postgres $dbname > /tmp/backup_postgres/$dbname.sql"
done
#rm -rf /tmp/backup_postgres
