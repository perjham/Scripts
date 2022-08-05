#!/bin/bash
MYSQL_PASSWORD="PERjham43882642\$\$"
for DB in $(mysql -e 'show databases' -s --skip-column-names -p$MYSQL_PASSWORD); do
    mysqldump -u root -p$MYSQL_PASSWORD $DB --skip-lock-tables > $DB.sql;
done
