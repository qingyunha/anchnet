from celery import Celery
import time
from pexpect_ssh import sshClient

app = Celery('tasks', broker='redis://localhost')

@app.task
def unblock_ips(login_info, ips, delay):
    time.sleep(delay)
    ssh = sshClient(login_info)
    ssh.run('unblock', ips)
    ssh.terminate(force=True)

