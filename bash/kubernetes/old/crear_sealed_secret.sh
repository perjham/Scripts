#!/bin/bash
echo "Nombre del namespace:"
read NS
echo "Usuario de conexión:"
read USERNAME
echo "Contraseña del usuario:"
read PASSWORD
echo "Nombre del secret (credenciales-bd por ejemplo):"
read SECRET_NAME
kubectl -n $NS create secret generic $SECRET_NAME --from-literal=username=$USERNAME --from-literal=password=$PASSWORD --dry-run=client -ojson > $SECRET_NAME.json
kubeseal < $SECRET_NAME.json > $SECRET_NAME-sealed.json
kubectl -n $NS create -f $SECRET_NAME-sealed.json
kubectl -n $NS get secret $SECRET_NAME
rm -rf $SECRET_NAME-sealed.json $SECRET_NAME.json
