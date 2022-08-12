#!/usr/bin/python3.8

import subprocess
import codecs
#import optparse
import re
import argparse
import base64
import sys
import os
from genericpath import exists
import jinja2
from flask import render_template, Flask
#from ..functions import file2base64

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ExecuteCommand():
    def __init__(self,*args):
        self.result = subprocess.Popen(args[0], stdout=subprocess.PIPE)
        for i in args[1:]:
            self.result = subprocess.Popen(i, stdin=self.result.stdout, stdout=subprocess.PIPE)
        self.result = codecs.decode(self.result.stdout.read(), 'UTF-8')
        self.result = re.sub(r'\n^$', '', self.result, flags=re.MULTILINE)

    def stdout(self):
        return self.result

class FileToBase64():
    def __init__(self,file):
        self.file = file

    def data(self):
        #print (base64.b64encode(open(self.file, 'rb').read()).decode('utf-8'))
        return base64.b64encode(open(self.file, 'rb').read()).decode('utf-8')

class CreateKubernetesAccess():
    parser = argparse.ArgumentParser(description='Command to create a Kubernetes access')
    parser.add_argument("-u", "--username", type=str, help="Kubernetes username")
    parser.add_argument("-n", "--namespace", type=str, help="Kubernetes namespace")
    parser.add_argument("-r", "--role", type=str, choices=['admin', 'monitor'], help="Rol")
    parser.add_argument("-k", "--kubernetes-keypath", type=str, default="/etc/kubernetes/pki", help="Kubernetes keys path")
    parser.add_argument("-o", "--users-keypath", type=str, default="/etc/kubernetes/pki/usuarios", help="Directory to save the keys, default /etc/kubernetes/pki/usuarios")
    args = parser.parse_args()
    if not args.username:
        parser.error("[-] Username is required, use --help for more information")
    elif not args.namespace:
        parser.error("[-] Namespace is required, use --help for more information")
    elif not args.role:
        parser.error("[-] Role is required, use --help for more information")

    def __init__(self):
        self.username = self.args.username
        self.namespace = self.args.namespace
        self.role = self.args.role
        self.kubernetes_keypath = self.args.kubernetes_keypath
        self.users_keypath = self.args.users_keypath
        # Construct role binding
        self.role_binding = self.username + "-" + self.role
        # Construct the path where the user keys will be stored
        self.user_keypath = self.users_keypath + "/" + self.username
        self.user_key = self.user_keypath + "/" + self.username + ".key"
        self.user_csr = self.user_keypath + "/" + self.username + ".csr"
        self.user_crt = self.user_keypath + "/" + self.username + ".crt"
        # Set the certificates
        self.kubernetes_crt_file = self.kubernetes_keypath + "/ca.crt"
        self.user_crt_file = self.user_keypath + "/" + self.username + ".crt"
        self.user_key_file = self.user_keypath + "/" + self.username + ".key"

    def options(self):
        return self.username, self.namespace, self.role, self.kubernetes_keypath, self.user_keypath

    def create_keys(self):
        # Searching for existing role binding
        get_user = ExecuteCommand(["kubectl", "get", "rolebindings.rbac.authorization.k8s.io", "--all-namespaces"],["grep", self.username])
        get_user = get_user.stdout()
        get_user = get_user.replace('\n','\n        ')
        if not exists(self.kubernetes_keypath):
            print("[ " + '\U0001F6A7' + "  ] Directory " + self.kubernetes_keypath + " doesn't exists.")
            print("       Set the correct --kubernetes-keypath with the kuberentes keys. Try use default path /etc/kubernetes/pki")
            sys.exit()
        elif get_user:
            # Showing the rolebindings found
            print("[ " + '\U0001F6A7' + "  ] Kubernetes user " + '"' + self.username + '"' + " already exists in at least one namespace.")
            print("        Rolebindngs found (namespace/rolebinding/role/time created):" )
            print(bcolors.WARNING + "        " + get_user + bcolors.ENDC)
            if exists(self.users_keypath):
                print("[ " + '\U0001F565' + "  ] Analizing --user-keypath provided (" + self.users_keypath + ")")
                print("[ " + '\U0001F4C1' + "  ] Directory " + self.users_keypath + " already exists.")
                if exists(self.user_keypath):
                    print("[ " + '\U0001F4C1' + "  ] Directory " + self.user_keypath + " already exists.")
                    
                    if not exists(self.user_key) or not exists(self.user_key) or not exists(self.user_crt):
                        print("[ " + '\U0001F6A8' + "  ] Keys for user " + '"' + self.username + '"' + " not found in " + self.user_keypath)
                        print("       Set the correct --user-keypath with the user's keys.")
                        print("       Remember, you must use the keys pair of created user.")
                        sys.exit()
                    else:
                        print("[ " + '\U0001F6A8' + "  ] User keys already exists, kubeconfig will be create with this keys.")
                else:
                    print("[ " + '\U0001F6A8' + "  ] Directory " + self.user_keypath + " doesn't exists.")
                    print("       Set the correct --user-keypath with the user's keys.")
                    print("       Remember, you must use the keys pair of created user.")
                    sys.exit()
            else:
                print("[ " + '\U0001F6A8' + "  ] Directory " + self.users_keypath + " doesn't exists.")
                print("       Set the correct --user-keypath with the user's keys.")
                print("       Remember, you must use the keys pair of created user.")
                sys.exit()
        else:
            print("[ " + '\U0001F64D' + "  ] User " + '"' + self.username + '"' + " seems not exist, user will be created...")
            if not exists(self.users_keypath):
                print("[ " + '\U0001F4C2' + "  ] Creating " + self.users_keypath + "...")
                os.mkdir(str(self.users_keypath))    
            print("[ " + '\U0001F4C2' + "  ] Cleaning" + self.user_keypath + "...")
            ExecuteCommand(["rm", "-rf", self.user_keypath + "/", "*"])
            print("[ " + '\U0001F6A7' + "  ] Creating " + self.user_keypath + "...")
            # Creating the folder containing user keys
            os.mkdir(str(self.user_keypath))
            #user_key = self.user_keypath + "/" + self.username + ".key"
            #user_csr = self.user_keypath + "/" + self.username + ".csr"
            #user_crt = self.user_keypath + "/" + self.username + ".crt"
            kubernetes_crt = self.kubernetes_keypath + "/ca.crt"
            kubernetes_key = self.kubernetes_keypath + "/ca.key"
            print("[ " + '\U0001F510' + "  ] Creating public/private keys for user " + self.username + " into " + self.user_keypath)
            print("[ " + '\U0001F5DD' + "   ] Creating key: " + self.user_key)
            # Createing the kyes signed by kubernetes
            ExecuteCommand(["openssl", "genrsa", "-out", self.user_key, "2048"])
            print("[ " + '\U0001F5DD' + "  ] Creating request: " + self.user_csr)
            ExecuteCommand(["openssl", "req", "-new", "-key", self.user_key, "-out", self.user_csr, "-subj", "/CN="+ self.username + "/O=grupo"])
            print("[ " + '\U0001F5DD' + "  ] Creating private key: " + self.user_crt)
            ExecuteCommand(["openssl", "x509", "-req", "-in", self.user_csr, "-CA", kubernetes_crt, "-CAkey", kubernetes_key, "-CAcreateserial", "-out", self.user_crt, "-days", "3650"])
            ExecuteCommand(["kubectl", "config", "set-credentials", self.username, "--client-certificate=" + self.user_crt, "--client-key=" + self.user_key ])

    def create_rb_manifest(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="templates")
        env = jinja2.Environment(loader=templateLoader)
        template = env.get_template("rolebinding.yml")
        app = Flask(__name__)
        with app.app_context():
            self.manifest = render_template(template, role=self.role, namespace=self.namespace, username=self.username)
        #return self.manifest

    def apply_rb_manifest(self):
        print("[ " + '\U0001F565' + "  ] Verifying if rolebinding already exists in namespace:", '"' + self.namespace + '"')
        get_user_rol = ExecuteCommand(["kubectl", "-n", self.namespace, "get", "rolebindings.rbac.authorization.k8s.io"],["grep", self.role_binding])
        get_user_rol = get_user_rol.stdout()
        if get_user_rol:
            # Showing the role binding founded
            print("[ " + '\U0001F6A7' + "  ] Rolebindngs found in namespace:", '"' + self.namespace + '", no new roles will be deployed...')
            describe_rolebing = ExecuteCommand(["kubectl", "-n", self.namespace, "describe", "rolebindings.rbac.authorization.k8s.io", self.role_binding])
            describe_rolebing = describe_rolebing.stdout()
            describe_rolebing = describe_rolebing.replace('\n','\n        ')
            print(bcolors.WARNING + "        " + describe_rolebing + bcolors.ENDC)
        else:
            print("[ " + '\U0001F6A8' + "  ] Rolebinding doesn't exists in namespace: ", '"' + self.namespace + '"' + ", creating it...")
            self.create_rb_manifest()
            with open("/tmp/rb.yml", "w") as temporal_file:
                print(self.manifest, file=temporal_file)
                temporal_file.close()
            ExecuteCommand(["kubectl", "apply", "-f", "/tmp/rb.yml"])
    
    def encode_keys(self):
        # Encode content of kubernetes_crt_file in base64 into "certificate_authority_data" var
        if exists(self.kubernetes_crt_file):
            self.certificate_authority_data = FileToBase64(self.kubernetes_crt_file).data()
        else:
            print("[ " + '\U0001F6A8' + "  ] kuberentes keys not found. Are you sure set the correct --keys, Please try again.")
            sys.exit()
        # Encode content of user_crt_file in base64 into "client_certificate_data" var
        if exists(self.user_crt_file):
            self.client_certificate_data = FileToBase64(self.user_crt_file).data()
        else:
            print("[ " + '\U0001F6A8' + "  ] Preview User keys not found. Are you sure set the correct --user-keypath, Please try again.")
            sys.exit()
        # Encode content of user_key_file in base64 into "client_key_data" var
        self.client_key_data = FileToBase64(self.user_key_file).data()
        self.create_kubeconfig()
        #print("HOLAS")
        #return self.certificate_authority_data, self.client_certificate_data, self.client_key_data

    def create_kubeconfig(self):
        context_name = ExecuteCommand(["kubectl", "config", "current-context"]).stdout()
        cluster_name = ExecuteCommand(["kubectl", "config", "view", "-o", 'jsonpath={.contexts[?(@.name==\"'+ context_name + '\")].context.cluster}']).stdout()
        server_name = ExecuteCommand(["kubectl", "config", "view", "-o", 'jsonpath={.clusters[?(@.name==\"'+ cluster_name + '\")].cluster.server}']).stdout()
        templateLoader = jinja2.FileSystemLoader(searchpath="templates")
        env = jinja2.Environment(loader=templateLoader)
        kubeconfig = env.get_template("kubeconfig")
        app = Flask(__name__)
        with app.app_context():
            self.create_kubeconfig = render_template(kubeconfig, namespace=self.namespace, username=self.username, certificate_authority_data=self.certificate_authority_data, server_name=server_name, cluster_name=cluster_name, client_certificate_data=self.client_certificate_data, client_key_data=self.client_key_data )
        kubeconfig = self.user_keypath + "/" "kubeconfig-" + self.username
        with open(kubeconfig, 'w') as file:
            print(self.create_kubeconfig, file=file)
        #kubeconfig = self.user_keypath + "/" "kubeconfig-" + self.username
        print("[ " + '\U0001F6E0' + "  ] Congratulations!!! Kubeconfig created as: " + kubeconfig)
            

# Steps

create_kubernetes_access = CreateKubernetesAccess()
create_kubernetes_access.create_keys()
create_kubernetes_access.apply_rb_manifest()
create_kubernetes_access.encode_keys()



