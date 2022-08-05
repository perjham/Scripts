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