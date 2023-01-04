#!/bin/bash
#
# Script para crear un usuario de kubernetes tipo "Client certificates", Rol admin sobre
# el namespace y asignar dicho Rol al usuario mediante un RolBinding
#

read -p "Nombre del usuario: " usuario
#usuario=$1
read -p "Nombre del namespace: " namespace
#namespace=$2
#grupo=$3
contexto=default
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
  #echo -e "Creando contexto asociado a usuario y namespace:"
  #kubectl config set-context $contexto --cluster=$cluster_name --namespace=$namespace --user=$usuario
else
  echo -e "El usuario $usuario ya existe"
  #echo -e "Creando contexto asociado a usuario y namespace:"
  #kubectl config set-context $contexto --cluster=$cluster_name --namespace=$namespace --user=$usuario
fi

cat > .role.yaml << EOF
kind: Role
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: admin
  namespace: $namespace
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: $usuario
  namespace: $namespace 
subjects:
- kind: User
  name: $usuario
  apiGroup: ""
roleRef:
  kind: Role
  name: admin
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
current-context: $contexto
contexts:
- context:
    cluster: $cluster_name
    namespace: $namespace
    user: $usuario
  name: $contexto
EOF
echo -e ""
echo -e "Certificados y kubeconfig creado en: $repo_llaves"
echo -e ""
