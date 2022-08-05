import subprocess

def pipeline():
    result = subprocess.Popen(["cat", "/proc/cpuinfo"], stdout=subprocess.PIPE)
    result = subprocess.Popen(["grep", "model name"], stdin=result.stdout, stdout=subprocess.PIPE)
    result = result.stdout.read()
    return result

result = pipeline()
print (result)