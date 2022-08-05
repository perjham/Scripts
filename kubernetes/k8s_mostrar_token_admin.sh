#!/bin/bash
echo ""
echo -n "El token para acceder al dashboard de Kubernetes como administrador total es:"
echo ""
echo ""
kubectl -n kubernetes-dashboard get secret $(kubectl -n kubernetes-dashboard get sa/admin-user -o jsonpath="{.secrets[0].name}") -o go-template="{{.data.token | base64decode}}"
echo ""
echo ""
