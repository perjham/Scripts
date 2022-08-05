import subprocess
import codecs
import optparse

def get_options():
    parser = optparse.OptionParser()
    parser.add_option("-a", "--any", dest = "option_a", help = "Option A")
    parser.add_option("-b", "--bro", dest = "option_b", help = "Option B")
    parser.add_option("-c", "--car", dest = "option_c", help = "Option C")
    (options,args) = parser.parse_args()
    if not options.option_a:
        parser.error("[-] Option A is required, use --help for more information")
    elif not options.option_b:
        parser.error("[-] Option B is required, use --help for more information")
    elif not options.option_c:
        parser.error("[-] Option C is required, use --help for more information")
    return options

# Read many arguments from a function
#def exec_command(*arguments):
#    command = [""]
#    for i in arguments:
#        command = command + [i]
#    del command[0]
#    command = subprocess.Popen(command)
#    return (command)

# ----------------------------------------------------------------

# Function to convert a byte string to UTF-8 string
# Example usage:
#   string = b'kubernetes-admin@kubernetes\n'
#   string = convert2uf8(string)
#   print (string)

def convert2uf8(string):
    string = codecs.decode(string, 'UTF-8')
    return string


# ----------------------------------------------------------------

# Function to execute any command on linux, just pas the entire command as a string
# Example usage: 
#   cmd1= ["kubectl", "get", "rolebindings.rbac.authorization.k8s.io", "--all-namespaces"]
#   result_cmd1 = execute_command(cmd1)
#   print (result_cmd1)

def execute_command(command):
    result = subprocess.Popen(command,stdout=subprocess.PIPE)
    result = result.stdout.read()
    result = convert2uf8(result)
    return result

# ----------------------------------------------------------------

# Function to concatenate multiple command line arguments (through pipeline)
# Example usage: 
#   cmd1= ["kubectl", "get", "rolebindings.rbac.authorization.k8s.io", "--all-namespaces"]
#   cmd2 = ["grep", "admin"]
#   cmd3 = ["grep", "ima"]
#   cmd4 = ["grep", "qa"]
#   result = pipeline(cmd1, cmd2, cmd3, cmd4)
#   print (result)

def pipeline(*arguments):
    result = subprocess.Popen(arguments[0], stdout=subprocess.PIPE)
    for i in arguments[1:]:
        result = subprocess.Popen(i, stdin=result.stdout, stdout=subprocess.PIPE)
    result = result.stdout.read()
    result = convert2uf8(result)
    return result

# ----------------------------------------------------------------



