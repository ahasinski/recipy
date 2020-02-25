import subprocess32 as subprocess
import shlex

def load_script_template(file, *args):
    with open(file, 'rb') as file:
        script = file.read()
    for n, arg in enumerate(args):
        old_arg = "${}".format(n)
        script = script.replace(old_arg, arg)
    return script

def run_script(script):
    subprocess.run(script,
        #shlex.split(script, posix=False),
        shell=True,
        check=True,
        #text=True,
        )
    return None

def load_run_script(file, *args):
    script = load_script_template(file, *args)
    run_script(script)
    return None