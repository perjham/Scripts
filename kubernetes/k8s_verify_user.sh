#!/bin/bash

echo ""
read -p "Ingresa el nombre de usuario: " USER

USER_NS_ACCESS=$(kubectl get rolebindings.rbac.authorization.k8s.io --all-namespaces  | grep -e "-admin" -e "-monitor" | grep "$USER" | awk '{print $1 "," $2}' | sort -u)

if [ -z "$USER_NS_ACCESS" ]
then
  echo "Usuario $USER no existe"
else
  echo ""
  echo "Usuario $USER tiene acceso a los siguientes namespaces:"
  echo ""
  for i in $USER_NS_ACCESS; do
    NS=$(echo $i | awk -F, '{print $1}')
    ROL=$(echo $i | awk -F, '{print $2}' | awk -F- '{print $2}')
    echo "$NS con rol $ROL"
  done
  echo ""
fi
