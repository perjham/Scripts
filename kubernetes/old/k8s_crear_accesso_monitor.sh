#!/bin/bash
#
# Script based on https://jeremievallee.com/2018/05/28/kubernetes-rbac-namespace-user.html
#
# In honor of the remarkable Windson
read -p "Nombre del namespace: " namespace

if [[ -z "$namespace" ]]; then
	echo "Use "$(basename "$0")" NAMESPACE";
	exit 1;
fi

echo -e "
apiVersion: v1
kind: ServiceAccount
metadata:
  name: $namespace-monitor
  namespace: $namespace
---
kind: Role
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: $namespace-monitor
  namespace: $namespace
rules:
- apiGroups: ['*'] 
  resources: ["pods", "pods/log", "deployments"]
  #verbs: ["get", "watch", "list", "patch"]
  verbs: ["get", "watch", "list"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: $namespace-monitor
  namespace: $namespace
subjects:
- kind: ServiceAccount
  name: $namespace-monitor
  namespace: $namespace
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: $namespace-monitor" | kubectl apply -f -

tokenName=$(kubectl get sa $namespace-monitor -n $namespace -o 'jsonpath={.secrets[0].name}')
token=$(kubectl get secret $tokenName -n $namespace -o "jsonpath={.data.token}" | base64 -d)
certificate=$(kubectl get secret $tokenName -n $namespace -o "jsonpath={.data['ca\.crt']}")

context_name="$(kubectl config current-context)"
cluster_name="$(kubectl config view -o "jsonpath={.contexts[?(@.name==\"${context_name}\")].context.cluster}")"
server_name="$(kubectl config view -o "jsonpath={.clusters[?(@.name==\"${cluster_name}\")].cluster.server}")"

echo -e "apiVersion: v1
kind: Config
preferences: {}

clusters:
- cluster:
    certificate-authority-data: $certificate
    server: $server_name
  name: $cluster_name

users:
- name: $namespace-monitor
  user:
    as-user-extra: {}
    client-key-data: $certificate
    token: $token

contexts:
- context:
    cluster: $cluster_name
    namespace: $namespace
    user: $namespace-monitor
  name: $namespace

current-context: $namespace" > /tmp/kubeconfig_$namespace
echo ""
echo "********************************************************************************************************"
echo "kubeconfig para el namespace: '$namespace' fue creado en /tmp/kubeconfig_$namespace"
echo "********************************************************************************************************"
echo ""
