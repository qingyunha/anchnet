import sys
import re
import time
import json
from datetime import datetime, timedelta
import logging

import pexpect

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('ssh.log')
fh.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


class Command(object):
    """The COMMAND interface"""

    command = ''

    def __init__(self, ssh):
        self.ssh = ssh

    def execute(self):
        raise NotImplementedError

    def __str__(self):
        return str(self.command)


class BlockCommand(Command):

    command = 'ip route-static %s 255.255.255.255 NULL 0'

    def execute(self, ips):
        for block_ip in ips:
            out = self.ssh.send_command(self.command % block_ip)


class UnblockCommand(Command):

    command = 'undo ip route-static %s 255.255.255.255'

    def execute(self, ips, delay=None):
        if delay is not None:
            delta = timedelta(seconds=delay)
            run_date = datetime.now() + delta
            print "tast run at ", run_date
            args = (self.ssh.login_info, ips)
            scheduler.add_job(unblock_ips_task, 'date', args, run_date=run_date)
        else:
            for block_ip in ips:
                out = self.ssh.send_command(self.command % block_ip)


class Route_tableCommand(Command):

    command = 'display ip routing-table' 

    def execute(self):
        s = self.ssh.send_command(self.command)
        return s 


class Config_includeCommand(Command):

    command = 'display current-configuration | include %s'
    def execute(self,ip):
        self.command = self.command % ip
        s = self.ssh.send_command(self.command)
        return s 


class Display_configCommand(Command):

    command = 'display current-configuration'
    def execute(self):
        TERM_CHAR = re.compile("\x1b\[42D\s*\x1b\[42D")
        self.command = self.command
        s = self.ssh.send_command(self.command)
        config = TERM_CHAR.sub("", s)
        return s[s.find("\n"):]


class sshClient(object):
    """The CLIENT class"""
    def __init__(self, host, user, passwd):
        self.ssh = Ssh(host, user, passwd) 
        self.commands = globals()

    def run(self, cmd, *args, **kargs):
        cmd = cmd.strip().capitalize()
        commd  = self.commands.get(cmd + 'Command') 
        if commd:
            return commd(self.ssh).execute(*args, **kargs)
        else:
            logger.warn('No such command: %s' % cmd)


class Ssh(object):
   
    ERROR = 'Error'
    PROMPT = r'<\S+\>'
    SPROMPT = r'\[\S+\]'
    MORE = '---- More ----'

    def __init__(self, host, user, passwd):
        # ssh_line = 'ssh -o StrictHostKeyChecking=no %s@%s'
        try:
            self.ssh = pexpect.spawn('ssh -1  %s@%s' % (user, host))
            self.ssh.logfile = open(host, 'ab')
            self.ssh.expect('password')
            self.ssh.sendline(passwd)
            self.ssh.expect(self.PROMPT)
            logger.info('login to %s success' % host)
            self.send_command('system-view')
        except Exception,e:
            logger.info('login failed')
            raise e

    def send_command(self, com):
        self.ssh.sendline(com)
        logger.info(com)
        ret = ""
        while True:
            try:
                index = self.ssh.expect([self.ERROR,
                                        self.SPROMPT,
                                        self.PROMPT,
                                        self.MORE]) 
                if index == 0:
                    logger.error('execute "%s" error' % (com))
                    self.ssh.expect([self.SPROMPT, self.PROMPT]) 
                    return ''
                elif index == 3:
                    self.ssh.send(" ")
                    ret = ret + self.ssh.before
                else:
                    return ret + self.ssh.before
            except pexpect.TIMEOUT, pexpect.EOF:
                logger.error('execute "%s" failed' % (com))
                return ''
        return ret

    def isalive(self):
        r = self.ssh.sendline()
        return True if r else False



if __name__ == "__main__":
    ssh = sshClient('10.155.1.211', 'sunc', 'www.51idc.com') 
    print ssh.run('Display_config')
