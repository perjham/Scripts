from asyncio.subprocess import DEVNULL
import subprocess
import codecs
import optparse
import re
import base64

# ----------------------------------------------------------------

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

# ----------------------------------------------------------------

# Function to create a CLI
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

# ----------------------------------------------------------------

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

# Function to eexecute any command on linux, just pass the entire command as a string
# Example usage: 
#   cmd1 = ["kubectl", "get", "rolebindings.rbac.authorization.k8s.io", "--all-namespaces"]
#   cmd2 = ["free", "-m"]
#   cmd3 = ["kubectl", "config", "view", "-o", 'jsonpath={.contexts[?(@.name==\"'+ "kubernetes-admin@kubernetes" + '\")].context.cluster}']
#   r1 = execute_command (cmd1)
#   print (r1)
#   r2 = execute_command (cmd2)
#   print (r2)
#   r3 = execute_command (cmd3)
#   print (r3)

def execute_command(command):
    result = subprocess.check_output(command)
    result = convert2uf8(result)
    # Remove the last line blank if exists
    # https://stackoverflow.com/questions/1140958/whats-a-quick-one-liner-to-remove-empty-lines-from-a-python-string#:~:text=one%20would%20be%3A-,%27%5Cn%5E%24%27,-%E2%80%93%C2%A0
    result = re.sub(r'\n^$', '', result, flags=re.MULTILINE)
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

def concatenate_commands(*arguments):
    result = subprocess.Popen(arguments[0], stdout=subprocess.PIPE)
    for i in arguments[1:]:
        result = subprocess.Popen(i, stdin=result.stdout, stdout=subprocess.PIPE)
    result = result.stdout.read()
    result = convert2uf8(result)
    # Remove the last blank line generate for the function
    result = re.sub(r'\n^$', '', result, flags=re.MULTILINE)
    return result

# ----------------------------------------------------------------

# Function to codify a filename in base64 format

def file2base64(filename):
    with open(filename, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

