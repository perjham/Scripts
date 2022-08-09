#!/bin/bash
#
# Script que realiza backup diferencial a traves de un backup completo (el cual es realizado la primera vez)
# Creado Por Alberto Vidal Alegria
#

HOSTNAME=`hostname -s`
BACKUP_HOME=/backup
TMP=/tmp
RSYNC_EXE=/usr/bin/rsync
DATA=("/etc" "/root/Scripts" "/var/spool/cron" "/opt")
SERVICIOS=("docker") # Servicios necesarios que esten apagados para la integridad del respaldo 
DATE=`date +%d%m%y-%H%M%S`
MAX_DAY_BACKUP=25
MYSQL_PASSWORD='WLUEN23Fbmu4wgZg9epMMNNv9MgSPdWq'

# --
# Apagamos los servicios indicados
# --
for i in "${SERVICIOS[@]}"; do
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` Apagando servicio $i"                              	| tee -a $TMP/backup-$DATE.log
  systemctl stop $i
done

# --
# Comenzamos el respaldo.
# Si no existe la carpeta donde se guardaran los respaldos (BACKUP_HOME), se crea
# --
if [ ! -d "$BACKUP_HOME" ]; then
# if [ ! -d "directorio" ] verifica si la carpeta no existe.
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` Verificando existencia de carpeta $BACKUP_HOME"  	| tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` Carpeta $BACKUP_HOME NO EXISTE"    	      		| tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` Creando carpeta $BACKUP_HOME"    		      	| tee -a $TMP/backup-$DATE.log
  a=`date "+%d:%m:%Y %H:%M:%S"`
  b=`mkdir -v $BACKUP_HOME`
  echo "$a $b"                                                                                  | tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` Inicio de respaldo"                              	| tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee -a $TMP/backup-$DATE.log
else
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` Verificando existencia de carpeta $BACKUP_HOME"  	| tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` Carpeta $BACKUP_HOME EXISTE"	   	      	        | tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` Inicio de respaldo"                              	| tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee -a $TMP/backup-$DATE.log
fi

# --
# Creamos el respaldo
# --

# Verificamos si la carpeta esta vacia listando el contenido, si esta vacia se crea el primer respaldo, es decir el respaldo completo
if [ -z "$(ls -A $BACKUP_HOME)" ];then
  a=`date "+%d:%m:%Y %H:%M:%S"`
  # Al crear la variable b, se crea la carpeta que indica dicha variable
  b=`mkdir -vp $BACKUP_HOME/full-$DATE`
  # Unicamente para mostar en log este paso
  echo "$a $b" 										| tee -a $TMP/backup-$DATE.log
  for i in "${DATA[@]}"; do
    echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee -a $TMP/backup-$DATE.log
    echo -e "`date "+%d:%m:%Y %H:%M:%S"` Respaldando $i"                                  	| tee -a $TMP/backup-$DATE.log
    # Quitamos el "/" a las rutas a respaldar para que se guarden como: "ruta_directorio_respaldar"
    FLY=$BACKUP_HOME/fly
    echo $i > $FLY
    # Quitamos el primer "/", por ejemplo si es "/etc/sysconfig" quedara "etc/sysconfig"
    sed -i 's/^\///' $FLY 
    # Cambiamos los demas "/" port "_" del resultado anterior, si es "etc/sysconfig" quedara "etc_sysconfig"
    sed -i 's/\//_/g' $FLY 
    # Crearmos la variable FLY2 con el nombre de la carpeta a respaldar final que deseamos (sin "/")
    FLY2=`cat $FLY`
    # Borramos la variable temporal creada que ya no servira mas.
    rm -rf $FLY
    #$RSYNC_EXE -az --delete --numeric-ids --log-file=$BACKUP_HOME/.log $i/  $BACKUP_HOME/full-$DATE/$FLY2
    $RSYNC_EXE -az --delete --numeric-ids --log-file=$BACKUP_HOME/.log $i/  $BACKUP_HOME/full-$DATE/$FLY2
    cat $BACKUP_HOME/.log >> $TMP/backup-$DATE.log 
    rm -rf $BACKUP_HOME/.log
  done
  RUTA_DE_BACKUP_ACTUAL=$BACKUP_HOME/full-$DATE
  mv $TMP/backup-$DATE.log $BACKUP_HOME/full-$DATE/
# Creamos el respaldo diferencial en base al respaldo completo
else
  a=`date "+%d:%m:%Y %H:%M:%S"`
  # Al crear la variable b, se crea la carpeta que indica dicha variable
  b=`mkdir -vp $BACKUP_HOME/incremental-$DATE`
  # Unicamente para mostar en log este paso
  echo "$a $b"    									   	| tee -a $TMP/backup-$DATE.log           
  for i in "${DATA[@]}"; do
    echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"    	| tee -a $TMP/backup-$DATE.log
    echo -e "`date "+%d:%m:%Y %H:%M:%S"` Respaldando $i"                                  	| tee -a $TMP/backup-$DATE.log
    # Quitamos el "/" a las rutas a respaldar para que se guarden como: "ruta_directorio_respaldar"
    FLY=$BACKUP_HOME/fly
    echo $i > $FLY
    # Quitamos el primer "/", por ejemplo si es "/etc/sysconfig" quedara "etc/sysconfig"
    sed -i 's/^\///' $FLY 
    # Cambiamos los demas "/" port "_" del resultado anterior, si es "etc/sysconfig" quedara "etc_sysconfig"
    sed -i 's/\//_/g' $FLY 
    # Crearmos la variable FLY2 con el nombre de la carpeta a respaldar final que deseamos (sin "/")
    FLY2=`cat $FLY`
    # Borramos la variable temporal creada que ya no servira mas.
    rm -rf $FLY
    FULL_BACKUP=`ls $BACKUP_HOME | grep full`
    #$RSYNC_EXE -az --delete --numeric-ids --log-file=$BACKUP_HOME/.log --link-dest=$BACKUP_HOME/$FULL_BACKUP $i/ $BACKUP_HOME/incremental-$DATE/$FLY2
    $RSYNC_EXE -az --delete --numeric-ids --log-file=$BACKUP_HOME/.log --link-dest=$BACKUP_HOME/$FULL_BACKUP/$FLY2 $i/ $BACKUP_HOME/incremental-$DATE/$FLY2
    cat $BACKUP_HOME/.log >> $TMP/backup-$DATE.log 
    rm -rf $BACKUP_HOME/.log
  done
  # --
  # Borrando respaldos mas antiguos que MAX_DAY_BACKUP
  # --
  find $BACKUP_HOME/* -maxdepth 0 -type d -name 'incremental*' -mtime +$MAX_DAY_BACKUP | xargs rm -rf
  RUTA_DE_BACKUP_ACTUAL=$BACKUP_HOME/incremental-$DATE
fi

# --
# Prendemos los servicios indicados
# --
for i in "${SERVICIOS[@]}"; do
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` --------------------------------------------"            | tee -a $TMP/backup-$DATE.log
  echo -e "`date "+%d:%m:%Y %H:%M:%S"` Levantando servicio $i"                                    | tee -a $TMP/backup-$DATE.log
  systemctl start $i
done

# --
# Exportamos las BD mysql
# --
mkdir $RUTA_DE_BACKUP_ACTUAL/dumps_mysql
#for DB in $(mysql -e 'show databases' -s --skip-column-names -p$MYSQL_PASSWORD); do
#    mysqldump -u root -p$MYSQL_PASSWORD $DB --skip-lock-tables > $RUTA_DE_BACKUP_ACTUAL/dumps_mysql/$DB.sql;
#    sleep 10
#done
mysqldump -p$MYSQL_PASSWORD -uadmin -hwordpress.cm6kgjqdsbqj.us-east-2.rds.amazonaws.com wordpress > $RUTA_DE_BACKUP_ACTUAL/dumps_mysql/wordpress.sql

# --
# Exportamos las BD Posgresql
# --
#mkdir $RUTA_DE_BACKUP_ACTUAL/dumps_psql
#chown postgres $RUTA_DE_BACKUP_ACTUAL/dumps_psql
##su - postgres -c "pg_dumpall -U postgres > $RUTA_DE_BACKUP_ACTUAL/dumps_psql/all.sql"
#cat << EOF > /tmp/list_postgres_db.sh
#psql -qXtc "select datname from pg_catalog.pg_database where datname<>'template0'" template1
#EOF
#for DB in `su - postgres -c "sh /tmp/list_postgres_db.sh"`
#do
#  su - postgres -c "pg_dump -U postgres $DB > $RUTA_DE_BACKUP_ACTUAL/dumps_psql/$DB.sql"
#done

mv $TMP/backup-$DATE.log $RUTA_DE_BACKUP_ACTUAL/
