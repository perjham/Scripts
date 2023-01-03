#!/bin/bash

echo ""
echo "Se encontraron los siguientes usuarios creados:"
echo ""
kubectl get rolebindings.rbac.authorization.k8s.io --all-namespaces  | grep -e "-admin" -e "-monitor" | awk '{print $2}' | sort -u | awk -F- '{print $1}'
echo ""
