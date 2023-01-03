#!/usr/bin/env python
from genericpath import exists
import subprocess
import optparse
import re
import os
import sys
import base64
import codecs

def get_options():
    parser = optparse.OptionParser()
    parser.add_option("-u", "--username", dest = "username", help = "Kubernetes username")
    parser.add_option("-n", "--namespace", dest = "namespace", help = "Kubernetes namespace")
    parser.add_option("-r", "--role", dest = "role", help = "Roles are: admin or monitor")
    parser.add_option("-k", "--kubernetes-keypath", dest = "kubernetes_keys", default = "/etc/kubernetes/pki", help = "Kubernetes keys path, default /etc/kubernetes/pki")
    parser.add_option("-o", "--user-keypath", dest = "user_keys", default = "/etc/kubernetes/pki/usuarios", help = "Directory to save the keys")
    (options,args) = parser.parse_args()
    if not options.username:
        parser.error("[-] Username is required, use --help for more information")
    elif not options.namespace:
        parser.error("[-] Namespace is required, use --help for more information")
    elif not options.role:
        parser.error("[-] Role is required, use --help for more information")
    return options

def create_keys(username,role,user_keys,kubernetes_keys):
  print("")
  role_binding = username + "-" + role
  #users_list = str(subprocess.check_output(["kubectl", "config", "view", "-o", "jsonpath='{.users[*].name}'"]))
  get_rolebindings = subprocess.Popen(["kubectl", "get", "rolebindings.rbac.authorization.k8s.io", "--all-namespaces"], stdout=subprocess.PIPE)
  get_user_rol = subprocess.Popen(["grep", role_binding], stdin=get_rolebindings.stdout, stdout=subprocess.PIPE)
  get_user_rol = get_user_rol.stdout.read()
  user_key_path = user_keys + "/" + username 
  if not exists(kubernetes_keys):
    print("[ " + '\U0001F6A7' + "  ] Directory " + kubernetes_keys + " doesn't exists.")
    print("       Set the correct --kubernetes-keypath with the kuberentes keys. Try use default path /etc/kubernetes/pki")
    sys.exit()
  elif get_user_rol:
    print("[ " + '\U0001F6A7' + "  ] Kubernetes user " + '"' + username + '"' + " already exists in at least one namespace.")
    print("       Rolebindngs found (namespace/rolebinding/role):" )
    print("") 
    get_user_rol = get_user_rol.replace(b'\n',b'\n       ')
    get_user_rol = codecs.decode(get_user_rol, 'UTF-8')
    print("       " + str(get_user_rol))
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
    subprocess.call(["rm", "-rf", user_key_path + "/", "*"])
    print("[ " + '\U0001F6A7' + "  ] Creating " + user_key_path + "...")
    os.mkdir(str(user_key_path))
    user_key = user_key_path + "/" + username + ".key"
    user_csr = user_key_path + "/" + username + ".csr"
    user_crt = user_key_path + "/" + username + ".crt"
    kubernetes_crt = kubernetes_keys + "/ca.crt"
    kubernetes_key = kubernetes_keys + "/ca.key"
    print("[ " + '\U0001F510' + "  ] Creating public/private keys for user " + username + " into " + user_key_path)
    print("[ " + '\U0001F5DD' + "  ] Creating key: " + user_key_path + "/" + username + ".key")
    subprocess.call(["openssl", "genrsa", "-out", user_key, "2048"])
    print("[ " + '\U0001F5DD' + "  ] Creating request: " + user_key_path + "/" + username+".csr")
    subprocess.call(["openssl", "req", "-new", "-key", user_key, "-out", user_csr, "-subj", "/CN="+ username + "/O=grupo"])
    subprocess.call(["openssl", "x509", "-req", "-in", user_csr, "-CA", kubernetes_crt, "-CAkey", kubernetes_key, "-CAcreateserial", "-out", user_crt, "-days", "3650"])
    subprocess.call(["kubectl", "config", "set-credentials", username, "--client-certificate=" + user_crt, "--client-key=" + user_key ])

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
  get_rolebindings = subprocess.Popen(["kubectl", "-n", namespace, "get", "rolebindings.rbac.authorization.k8s.io"], stdout=subprocess.PIPE)
  get_user_rol = subprocess.Popen(["grep", role_binding], stdin=get_rolebindings.stdout, stdout=subprocess.PIPE)
  get_user_rol = get_user_rol.stdout.read()
  if get_user_rol:
    print("[ " + '\U0001F6A7' + "  ] Rolebindngs found in namespace:", '"' + namespace + '", no new roles will be deployed...')
    print ("")
    describe_rolebing = subprocess.check_output(["kubectl", "-n", namespace, "describe", "rolebindings.rbac.authorization.k8s.io", role_binding])
    describe_rolebing = describe_rolebing.replace(b'\n',b'\n       ')
    describe_rolebing = codecs.decode(describe_rolebing, 'UTF-8')
    print("       " + str(describe_rolebing))  
  else:
    print("[ " + '\U0001F6A8' + "  ] Rolebinding doesn't exists in namespace: ", '"' + namespace + '"' + " creating...")
    with open('/tmp/role.yml', 'w') as file:
        file.write(manifest)
    subprocess.call(["kubectl", "apply", "-f", "/tmp/role.yml"])
   

def encode_keys(username,user_keys,kubernetes_keys):
    # Encode content of kubernetes_crt_file in base64 into "certificate_authority_data" var
    kubernetes_crt_file = kubernetes_keys + "/ca.crt"
    print (username+user_keys+kubernetes_keys)
    if exists(kubernetes_crt_file):
      kubernetes_crt = subprocess.check_output(["cat", kubernetes_crt_file], text=True)
      #kubernetes_crt = subprocess.check_output(["cat", kubernetes_crt_file])
      kubernetes_crt_bytes = kubernetes_crt.encode("ascii")
      certificate_authority_data_bytes = base64.b64encode(kubernetes_crt_bytes)
      certificate_authority_data = certificate_authority_data_bytes.decode("ascii")
    else:
      print("[ " + '\U0001F6A8' + "  ] uberentes keys not found. Are you sure set the correct --keys, Please try again.")
      sys.exit()
    # Encode content of user_crt_file in base64 into "client_certificate_data" var
    user_crt_file = user_keys + "/" + username + "/" + username + ".crt"
    if exists(user_crt_file):
      user_crt = subprocess.check_output(["cat", user_crt_file], text=True)
      user_crt_bytes = user_crt.encode("ascii")
    else:
      print("[ " + '\U0001F6A8' + "  ] Preview User keys not found. Are you sure set the correct --user-keypath, Please try again.")
      sys.exit()
    client_certificate_data_bytes = base64.b64encode(user_crt_bytes)
    client_certificate_data = client_certificate_data_bytes.decode("ascii")
    # Encode content of user_key_file in base64 into "client_key_data" var
    user_key_file = user_keys + "/" + username + "/" + username + ".key"
    user_key = subprocess.check_output(["cat", user_key_file], text=True)
    user_key_bytes = user_key.encode("ascii")
    client_key_data_bytes = base64.b64encode(user_key_bytes)
    client_key_data = client_key_data_bytes.decode("ascii")
    return certificate_authority_data, client_certificate_data, client_key_data

def create_kubeconfig(certificate_authority_data,client_certificate_data,client_key_data,username,namespace,user_keys):
    # kubectl command add blank line to the end, we need to remove that line (\n)
    context_name = subprocess.check_output(["kubectl", "config", "current-context"])
    context_name = context_name.replace(b'\n',b'')
    context_name = codecs.decode(context_name, 'UTF-8')

    cluster_name = subprocess.check_output(["kubectl", "config", "view", "-o", 'jsonpath={.contexts[?(@.name==\"'+ context_name + '\")].context.cluster}'])
    cluster_name = cluster_name.replace(b'\n',b'')
    cluster_name = codecs.decode(cluster_name, 'UTF-8')

    server_name = subprocess.check_output(["kubectl", "config", "view", "-o", 'jsonpath={.clusters[?(@.name==\"'+ cluster_name + '\")].cluster.server}'])
    server_name = server_name.replace(b'\n',b'')
    server_name = codecs.decode(server_name, 'UTF-8')

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
        print("[ " + '\U0001F6E0' + "  ] Kubeconfig created in: " + kubeconfig_file)

# Steps:

options = get_options()
create_keys(options.username,options.role,options.user_keys,options.kubernetes_keys)

role_binding = options.username + "-" + options.role
get_rolebindings = subprocess.Popen(["kubectl", "get", "rolebindings.rbac.authorization.k8s.io", "--all-namespaces"], stdout=subprocess.PIPE)
get_user_rol = subprocess.Popen(["grep", role_binding], stdin=get_rolebindings.stdout, stdout=subprocess.PIPE)
get_user_rol = get_user_rol.stdout.read()
user_key_path = options.user_keys + "/" + options.username
manifest = create_kubernetes_manifest(options.username,options.namespace,options.role)
apply_kubernetes_manifest(manifest,options.username,options.namespace,options.role)
certificate_authority_data, client_certificate_data, client_key_data = encode_keys(options.username,options.user_keys,options.kubernetes_keys)
create_kubeconfig(certificate_authority_data,client_certificate_data,client_key_data,options.username,options.namespace,options.user_keys)
