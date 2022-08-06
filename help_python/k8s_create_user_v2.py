#!/usr/bin/env python
from genericpath import exists
#import optparse
import os
import sys

from functions import *

def get_options():
    parser = optparse.OptionParser()
    parser.add_option("-u", "--username", dest = "username", help = "Kubernetes username")
    parser.add_option("-n", "--namespace", dest = "namespace", help = "Kubernetes namespace")
    parser.add_option("-r", "--role", dest = "role", help = "Roles are: admin or monitor")
    parser.add_option("-k", "--kubernetes-keypath", dest = "kubernetes_keys", default = "/etc/kubernetes/pki", help = "Kubernetes keys path, default /etc/kubernetes/pki")
    parser.add_option("-o", "--user-keypath", dest = "user_keys", default = "/etc/kubernetes/pki/usuarios", help = "Directory to save the keys, default /etc/kubernetes/pki/usuarios")
    (options,args) = parser.parse_args()
    if not options.username:
        parser.error("[-] Username is required, use --help for more information")
    elif not options.namespace:
        parser.error("[-] Namespace is required, use --help for more information")
    elif not options.role:
        parser.error("[-] Role is required, use --help for more information")
    return options

def create_keys(username,role,user_keys,kubernetes_keys):
  # Construct role binding
  role_binding = username + "-" + role
  # Searching for existing role binding
  get_user_rol = concatenate_commands(["kubectl", "get", "rolebindings.rbac.authorization.k8s.io", "--all-namespaces"],["grep", role_binding])
  # Construct the path where the user keys will be stored
  user_key_path = user_keys + "/" + username 
  if not exists(kubernetes_keys):
    print("[ " + '\U0001F6A7' + "  ] Directory " + kubernetes_keys + " doesn't exists.")
    print("       Set the correct --kubernetes-keypath with the kuberentes keys. Try use default path /etc/kubernetes/pki")
    sys.exit()
  elif get_user_rol:
    # Showing the rolebindings found
    print("[ " + '\U0001F6A7' + "  ] Kubernetes user " + '"' + username + '"' + " already exists in at least one namespace.")
    print("        Rolebindngs found (namespace/rolebinding/role/time created):" )
    print(bcolors.WARNING + "        " + get_user_rol + bcolors.ENDC)
    if exists(user_keys):
      print("[ " + '\U0001F565' + "  ] Analizing --user-keypath provided (" + user_keys + ")")
      print("[ " + '\U0001F4C1' + "  ] Directory " + user_keys + " already exists.")
      if exists(user_key_path):
        print("[ " + '\U0001F4C1' + "  ] Directory " + user_key_path + " already exists.")
        user_key = user_key_path + "/" + username + ".key"
        user_key = user_key_path + "/" + username + ".csr"
        user_crt = user_key_path + "/" + username + ".crt"
        if not exists(user_key) or not exists(user_key) or not exists(user_crt):
          print("[ " + '\U0001F6A8' + "  ] Keys for user " + '"' + username + '"' + " not found in " + user_key_path)
          print("       Set the correct --user-keypath with the user's keys.")
          print("       Remember, you must use the keys pair of created user.")
          sys.exit()
        else:
          print("[ " + '\U0001F6A8' + "  ] User keys already exists, kubeconfig will be create with this keys.")
      else:
        print("[ " + '\U0001F6A8' + "  ] Directory " + user_key_path + " doesn't exists.")
        print("       Set the correct --user-keypath with the user's keys.")
        print("       Remember, you must use the keys pair of created user.")
        sys.exit()
    else:
      print("[ " + '\U0001F6A8' + "  ] Directory " + user_keys + " doesn't exists.")
      print("       Set the correct --user-keypath with the user's keys.")
      print("       Remember, you must use the keys pair of created user.")
      sys.exit()
  else:
    print("[ " + '\U0001F64D' + "  ] User " + '"' + username + '"' + " seems not exist, user will be created...")
    if not exists(user_keys):
      print("[ " + '\U0001F4C2' + "  ] Creating " + user_keys + "...")
      os.mkdir(str(user_keys))    
    print("[ " + '\U0001F4C2' + "  ] Cleaning" + user_key_path + "...")
    execute_command(["rm", "-rf", user_key_path + "/", "*"])
    print("[ " + '\U0001F6A7' + "  ] Creating " + user_key_path + "...")
    # Creating the folder containing user keys
    os.mkdir(str(user_key_path))
    user_key = user_key_path + "/" + username + ".key"
    user_csr = user_key_path + "/" + username + ".csr"
    user_crt = user_key_path + "/" + username + ".crt"
    kubernetes_crt = kubernetes_keys + "/ca.crt"
    kubernetes_key = kubernetes_keys + "/ca.key"
    print("[ " + '\U0001F510' + "  ] Creating public/private keys for user " + username + " into " + user_key_path)
    print("[ " + '\U0001F5DD' + "   ] Creating key: " + user_key)
    # Createing the kyes signed by kubernetes
    execute_command(["openssl", "genrsa", "-out", user_key, "2048"])
    print("[ " + '\U0001F5DD' + "  ] Creating request: " + user_csr)
    execute_command(["openssl", "req", "-new", "-key", user_key, "-out", user_csr, "-subj", "/CN="+ username + "/O=grupo"])
    print("[ " + '\U0001F5DD' + "  ] Creating private key: " + user_crt)
    execute_command(["openssl", "x509", "-req", "-in", user_csr, "-CA", kubernetes_crt, "-CAkey", kubernetes_key, "-CAcreateserial", "-out", user_crt, "-days", "3650"])
    execute_command(["kubectl", "config", "set-credentials", username, "--client-certificate=" + user_crt, "--client-key=" + user_key ])

def create_kubernetes_manifest(username,namespace,role):
    manifest = '''\
kind: Role
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: ''' + role + \
  '''
  namespace: ''' + namespace
    # For admin rol set the rules to:
    if role == "admin":
        manifest = manifest + "\n" + '''\
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: ''' + username + "-" + role + \
  '''
  namespace: ''' + namespace + \
  '''
subjects:
- kind: User
  name: ''' + username + \
  '''
  apiGroup: ""
roleRef:
  kind: Role
  name: ''' + role + \
  '''
  apiGroup: ""'''
    # For monitor rol set the rules to:
    elif role == "monitor":
        manifest = manifest + "\n" + '''\
rules:
- apiGroups: ["*"]
  resources: ["secrets","namespaces","pods","pods/log","configmaps","services","events","namespaces","nodes","horizontalpodautoscalers","ingresses","servicemonitors","replicasets","deployments"]
  verbs: ["get", "watch", "list"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: ''' + username + "-" + role + \
  '''
  namespace: ''' + namespace + \
  '''
subjects:
- kind: User
  name: ''' + username + \
  '''
  apiGroup: ""
roleRef:
  kind: Role
  name: ''' + role + \
  '''
  apiGroup: ""'''    
    else:
        print('Valid roles are: "monitor" and "admin". Please, try again.')
        sys.exit()
    return manifest  

def apply_kubernetes_manifest(manifest,username,namespace,role):
  print("[ " + '\U0001F565' + "  ] Verifying if rolebinding already exists in namespace:", '"' + namespace + '"')
  role_binding = username + "-" + role
  get_user_rol = concatenate_commands(["kubectl", "-n", namespace, "get", "rolebindings.rbac.authorization.k8s.io"],["grep", role_binding])
  if get_user_rol:
    # Showing the role binding founded
    print("[ " + '\U0001F6A7' + "  ] Rolebindngs found in namespace:", '"' + namespace + '", no new roles will be deployed...')
    describe_rolebing = execute_command(["kubectl", "-n", namespace, "describe", "rolebindings.rbac.authorization.k8s.io", role_binding])
    describe_rolebing = describe_rolebing.replace('\n','\n        ')
    print(bcolors.WARNING + "        " + describe_rolebing + bcolors.ENDC)
  else:
    print("[ " + '\U0001F6A8' + "  ] Rolebinding doesn't exists in namespace: ", '"' + namespace + '"' + ", creating it...")
    with open('/tmp/role.yml', 'w') as file:
        file.write(manifest)
    execute_command(["kubectl", "apply", "-f", "/tmp/role.yml"]) 

def encode_keys(username,user_keys,kubernetes_keys):
    # Encode content of kubernetes_crt_file in base64 into "certificate_authority_data" var
    kubernetes_crt_file = kubernetes_keys + "/ca.crt"
    if exists(kubernetes_crt_file):
      certificate_authority_data = file2base64(kubernetes_crt_file)
    else:
      print("[ " + '\U0001F6A8' + "  ] kuberentes keys not found. Are you sure set the correct --keys, Please try again.")
      sys.exit()
    # Encode content of user_crt_file in base64 into "client_certificate_data" var
    user_crt_file = user_keys + "/" + username + "/" + username + ".crt"
    if exists(user_crt_file):
      client_certificate_data = file2base64(user_crt_file)
    else:
      print("[ " + '\U0001F6A8' + "  ] Preview User keys not found. Are you sure set the correct --user-keypath, Please try again.")
      sys.exit()
    # Encode content of user_key_file in base64 into "client_key_data" var
    user_key_file = user_keys + "/" + username + "/" + username + ".key"
    client_key_data = file2base64(user_key_file)
    return certificate_authority_data, client_certificate_data, client_key_data

def create_kubeconfig(certificate_authority_data,client_certificate_data,client_key_data,username,namespace,user_keys):
    context_name = execute_command(["kubectl", "config", "current-context"])
    cluster_name = execute_command(["kubectl", "config", "view", "-o", 'jsonpath={.contexts[?(@.name==\"'+ context_name + '\")].context.cluster}'])
    server_name = execute_command(["kubectl", "config", "view", "-o", 'jsonpath={.clusters[?(@.name==\"'+ cluster_name + '\")].cluster.server}'])

    kubeconfig_content='''\
apiVersion: v1
kind: Config
preferences: {}
clusters:
- cluster:
    certificate-authority-data: ''' + certificate_authority_data + \
    '''
    server: ''' + server_name + \
    '''
  name: ''' + cluster_name + \
    '''
users:
- name: ''' + username + \
    '''
  user:
    client-certificate-data: ''' + client_certificate_data + \
    '''
    client-key-data: ''' + client_key_data + \
    '''
current-context: ''' + username + \
    '''
contexts:
- context:
    cluster: ''' + cluster_name + \
    '''
    namespace: ''' + namespace + \
    '''
    user: ''' + username + \
    '''
  name: ''' + username

    kubeconfig_file = user_keys + "/" + username + "/" "kubeconfig-" + username
    with open(kubeconfig_file, 'w') as file:
        file.write(kubeconfig_content)
        print("[ " + '\U0001F6E0' + "  ] Congratulations!!! Kubeconfig created as: " + kubeconfig_file)

# Steps:

options = get_options()
create_keys(options.username,options.role,options.user_keys,options.kubernetes_keys)
manifest = create_kubernetes_manifest(options.username,options.namespace,options.role)
apply_kubernetes_manifest(manifest,options.username,options.namespace,options.role)
certificate_authority_data, client_certificate_data, client_key_data = encode_keys(options.username,options.user_keys,options.kubernetes_keys)
create_kubeconfig(certificate_authority_data,client_certificate_data,client_key_data,options.username,options.namespace,options.user_keys)