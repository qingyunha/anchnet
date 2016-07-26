import os
from os import path
from datetime import date

from ssh import sshClient

BACKUP_FOLDER = "data"


def backup(host, user, passwd):
    today = date.today()
    client = sshClient(host, user, passwd)
    config = client.run("DISPLAY_CONFIG")
    if config:
        d = path.join(BACKUP_FOLDER, host)
        if not path.exists(d):
            os.mkdir(d)
        filename = "{0!s}.txt".format(today)
        f = open(path.join(d, filename), "wb")
        f.write(config)
        f.close()


if __name__ == "__main__":
    backup('10.155.1.211', 'sunc', 'www.51idc.com') 
