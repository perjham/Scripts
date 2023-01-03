#!/bin/bash
#
# Versión 1.0
# Autor: Alberto Vidal Alegria
# Correo: alberto.vidal@unmsm.edu.pe 
#
# Este script realiza lo siguiente:
#
# - Crea un usuario del tipo "Client certificates"
# - Crea un ClusterRole con permisos definidos
# - Crear un ClusterRoleBinding que asocia el ClusterRole con el usuario para brindar los permisos
# - Crear el kubeconfig del usuario creado con los permisos definidos
#  
# Acesso a los recursos: "pods","pods/log","configmaps","services","events","namespaces","nodes",
# "horizontalpodautoscalers","ingresses","servicemonitors","replicasets","deployments" 
# Acciones permitidas en dichos recursos: "get", "watch", "list"
#
# En conclusion, creamos un acceso de usuario a todo el cluster con los permisos definido sobre los
# recursos definidos

read -p "Nombre del usuario: " usuario
repo_llaves=/etc/kubernetes/pki/usuarios/$usuario

context_name="$(kubectl config current-context)"
cluster_name="$(kubectl config view -o "jsonpath={.contexts[?(@.name==\"${context_name}\")].context.cluster}")"
echo -e "El nombre de clúster Kubernetes es: $cluster_name"
server_name="$(kubectl config view -o "jsonpath={.clusters[?(@.name==\"${cluster_name}\")].cluster.server}")"
echo -e "La dirección de conexion al API de Kubernetes es: $server_name"
existe_usuario=`kubectl config view -o jsonpath='{.users[*].name}' | grep $usuario`

if [ -z "$existe_usuario" ];then
  echo -e ""
  echo -e "***********************************************"
  echo -e  "Creando llaves ssl en la ubicacion $repo_llaves"
  echo -e "***********************************************"
  mkdir -p $repo_llaves
  echo -e "Creando llave privada $usuario.key:"
  echo -e ""
  openssl genrsa -out $repo_llaves/$usuario.key 2048
  echo -e ""
  echo -e "Creando request $usuario.csr:"
  openssl req -new -key $repo_llaves/$usuario.key -out $repo_llaves/$usuario.csr -subj "/CN=$usuario/O=grupo"
  echo -e ""
  echo -e "Creando llave publica $usuario.csr:"
  openssl x509 -req -in $repo_llaves/$usuario.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out $repo_llaves/$usuario.crt -days 3650
  echo -e ""
  echo -e "Creando usario en Kubernestes:"
  #kubectl config set-credentials $usuario --client-certificate-data=`cat $usuario.crt | base64` -w 0  --client-key-data=`cat $usuario.key | base64 -w 0`
  kubectl config set-credentials $usuario --client-certificate=$repo_llaves/$usuario.crt --client-key=$repo_llaves/$usuario.key
  echo -e ""
else
  echo -e "El usuario $usuario ya existe"
fi

cat > .role.yaml << EOF
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: cluster-monitor
rules:
- apiGroups: ["*"]
  resources: ["pods","pods/log","configmaps","services","events","namespaces","nodes","horizontalpodautoscalers","ingresses","servicemonitors","replicasets","deployments"]
  verbs: ["get", "watch", "list"]
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: $usuario-monitor
subjects:
- kind: User
  name: $usuario
  apiGroup: ""
roleRef:
  kind: ClusterRole
  name: cluster-monitor
  apiGroup: ""
EOF
kubectl apply -f ./.role.yaml

certificate_authority_data=`cat /etc/kubernetes/pki/ca.crt | base64 -w 0`
client_certificate_data=`cat $repo_llaves/$usuario.crt | base64 -w 0`
client_key_data=`cat $repo_llaves/$usuario.key | base64 -w 0`

echo -e "Creando archivo config para usuario $usuarios"
cat > $repo_llaves/kubeconfig-$usuario << EOF
apiVersion: v1
kind: Config
preferences: {}
clusters:
- cluster:
    certificate-authority-data: $certificate_authority_data
    server: $server_name
  name: $cluster_name
users:
- name: $usuario
  user:
    client-certificate-data: $client_certificate_data
    client-key-data: $client_key_data
current-context: default
contexts:
- context:
    cluster: $cluster_name
    namespace: $namespace
    user: $usuario
  name: default
EOF
echo -e ""
echo -e "Certificados y kubeconfig creados en: $repo_llaves"
echo -e ""
