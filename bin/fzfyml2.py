import sys
import yaml
from Task import Task
from Continue import Continue
import subprocess
from subprocess import PIPE

with open(sys.argv[2]) as f:
    yml = yaml.load(f, Loader=yaml.SafeLoader)
next_tasks = Continue(yml.get('continue', {}))
base_task = Task(yml['base_task'], next_tasks.get_expect())
task = base_task

if sys.argv[1] == 'run':
    while True:
        proc = subprocess.run(task.get_cmd(), shell=True, stdout=PIPE)
        result = proc.stdout.decode('utf8')
        if not task.is_continue(result):
            task.stdout(result)
            break
        else:
            next_task = next_tasks.get(result.split('\n')[1])
            task = base_task.create_continue_task(next_task)
elif sys.argv[1] == 'debug':
    print(base_task.get_cmd())
else:
    raise ValueError("")