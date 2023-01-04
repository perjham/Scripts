#!/bin/bash
NAMESPACE=$1
if [[ -z "$NAMESPACE" ]]; then
        echo "Use "$(basename "$0")" NAMESPACE";
        exit 1;
fi
kubectl get namespace $NAMESPACE -o json > $NAMESPACE.json
sed -i -e 's/"kubernetes"//' $NAMESPACE.json
kubectl replace --raw "/api/v1/namespaces/$NAMESPACE/finalize" -f ./$NAMESPACE.json > /dev/null 2>&1
rm -rf ./$NAMESPACE.json
kubectl get ns
