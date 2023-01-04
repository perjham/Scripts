#!/bin/bash
#
# Versión 1.0
# Autor: Alberto Vidal Alegria
# Correo: perjham@gmail.com
#
# Script para crear un usuario de kubernetes tipo "Client certificates", con Rol Administrador o Monitor sobre un namespace
# Rol Administrador:
#   apiGroups: ["*"]
#   resources: ["*"]
#   verbs: ["*"]
# Rol Monitor: 
#   apiGroups: ["*"]
#   resources: ["secrets","namespaces","pods","pods/log","configmaps","services","events","namespaces","nodes","horizontalpodautoscalers","ingresses","servicemonitors","replicasets","deployments"]
#    verbs: ["get", "watch", "list"]

echo -e ""
while [[ $usuario = "" ]]; do
  read -p "Por favor, escriba el nombre del usuario: " usuario
done
echo -e ""
echo -e "Espacios de trabajo actuales:"
echo -e "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"
kubectl get ns | awk '{print $1}' | grep -v NAME
echo -e ""
while [[ $namespace = "" ]]; do
  read -p "Por favor, escriba el nombre del espacio de trabajo: " namespace
  echo -e ""
done

echo -e "Descripción de roles:"
echo -e "+-+-+-+-+-+-+-+-+-+-+"
echo -e ""
echo -e "1) Administrador, permisos de lectura y escirtura sobre todos los recursos del namespace $namespace"
echo -e ""
echo -e "2) Monitor, permisos de lectura sobre los recursos del namespace $namespace"
echo -e ""
read -p "Rol [1|2]: " rol
echo -e ""
while [[ "$rol" != "1" && "$rol" != "2" ]]; do
  echo -e "Opción incorrecta"
  echo -e ""
  echo -e "Descripción de roles:"
  echo -e "+-+-+-+-+-+-+-+-+-+-+"
  echo -e ""
  echo -e "1) Administrador, permisos de lectura y escirtura sobre todos los recursos del namespace $namespace"
  echo -e ""
  echo -e "2) Monitor, permisos de lectura sobre los recursos del namespace $namespace"
  echo -e ""
  read -p "Rol [1|2]: " rol 
  echo -e ""
done

#contexto=default
repo_llaves=/etc/kubernetes/pki/usuarios/$usuario
context_name="$(kubectl config current-context)"
cluster_name="$(kubectl config view -o "jsonpath={.contexts[?(@.name==\"${context_name}\")].context.cluster}")"
#echo -e "El nombre de clúster Kubernetes es: $cluster_name"
server_name="$(kubectl config view -o "jsonpath={.clusters[?(@.name==\"${cluster_name}\")].cluster.server}")"
#echo -e "La dirección de conexion al API de Kubernetes es: $server_name"
existe_usuario=`kubectl config view -o jsonpath='{.users[*].name}' | grep $usuario`

# --------------------------------------------------------------------------
# Bucle para la creación de usuario con Rol Administrador sobre el namespace 
# ---------------------------------------------------------------------------

if [ "$rol" == 1 ]; then
  if [ -z "$existe_usuario" ]; then
    echo -e  "Creando llaves ssl en la ubicacion $repo_llaves"
    echo -e ""
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
    echo -e "El usuario $usuario ya existe, no se crearan nuevas llaves SSL..."
    #echo -e "Creando contexto asociado a usuario y namespace:"
    #kubectl config set-context $contexto --cluster=$cluster_name --namespace=$namespace --user=$usuario
    echo -e ""
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
  name: $usuario-admin
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
  kubectl apply -f ./.role.yaml > /dev/null 2>&1
  echo -e "Creando los permisos solicitados..."
  echo -e ""
  
  certificate_authority_data=`cat /etc/kubernetes/pki/ca.crt | base64 -w 0`
  client_certificate_data=`cat $repo_llaves/$usuario.crt | base64 -w 0`
  client_key_data=`cat $repo_llaves/$usuario.key | base64 -w 0`

  echo -e "Creando archivo kubeconfig para usuario $usuarios..."
  echo -e ""
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
current-context: $usuario
contexts:
- context:
    cluster: $cluster_name
    namespace: $namespace
    user: $usuario
  name: $usuario
EOF
  echo -e "Certificados SSL y archivo kubeconfig del usuario $usuario creados en: $repo_llaves"
  echo -e ""
  ls -l $repo_llaves

# -----------------------------------------------------------------------
# Bucle para la creación de usuario con Rol Monitor sobre el namespace
# -----------------------------------------------------------------------

else
  if [ -z "$existe_usuario" ]; then
    echo -e  "Creando llaves ssl en la ubicacion $repo_llaves"
    echo -e ""
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
    echo -e "El usuario $usuario ya existe, no se crearan nuevas llaves SSL..."
    #echo -e "Creando contexto asociado a usuario y namespace:"
    #kubectl config set-context $contexto --cluster=$cluster_name --namespace=$namespace --user=$usuario
    echo -e ""
  fi

  cat > .role.yaml << EOF
kind: Role
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: monitor
  namespace: $namespace
rules:
- apiGroups: ["*"]
  resources: ["secrets","namespaces","pods","pods/log","configmaps","services","events","namespaces","nodes","horizontalpodautoscalers","ingresses","servicemonitors","replicasets","deployments"]
  verbs: ["get", "watch", "list"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: $usuario-monitor
  namespace: $namespace 
subjects:
- kind: User
  name: $usuario
  apiGroup: ""
roleRef:
  kind: Role
  name: monitor
  apiGroup: ""
EOF
  kubectl apply -f ./.role.yaml > /dev/null 2>&1
  echo -e "Creando los permisos solicitados..."
  echo -e ""
  
  certificate_authority_data=`cat /etc/kubernetes/pki/ca.crt | base64 -w 0`
  client_certificate_data=`cat $repo_llaves/$usuario.crt | base64 -w 0`
  client_key_data=`cat $repo_llaves/$usuario.key | base64 -w 0`

  echo -e "Creando archivo kubeconfig para usuario $usuarios..."
  echo -e ""
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
current-context: $usuario
contexts:
- context:
    cluster: $cluster_name
    namespace: $namespace
    user: $usuario
  name: $usuario
EOF
  echo -e "Certificados SSL y archivo kubeconfig del usuario $usuario creados en: $repo_llaves"
  echo -e ""
  ls -l $repo_llaves
  echo -e ""
fi
