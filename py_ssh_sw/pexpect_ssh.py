import pexpect
import logging, sys
import threading, time
import json

logger = logging.getLogger('comm_ssh')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('comm_ssh.log')
fh.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)

def sleep_time(func, delay):
    def f(*args):
        time.sleep(delay)
        return func(*args)
    return f


class Switch(object):
    """The INVOKER class"""
    @classmethod
    def execute(cls, command, *args, **kwargs):
        if 'time' in kwargs:
            delay = kwargs['time']
            print 'sleep %d' % delay
            cm = sleep_time(command.execute, delay)
            t = threading.Thread(target=cm, args=args)
            t.start()
        else:
            return command.execute(*args)

class Command(object):
    """The COMMAND interface"""
    def __init__(self, obj):
        self._obj = obj

    def execute(self):
        raise NotImplementedError

class BlockCommand(Command):

    command = 'ip route-static %s 255.255.255.255 NULL 0'

    def execute(self, ips):
        for block_ip in ips:
            print self.command % block_ip 
            logger.info('block_ip %s' % block_ip)
            out = self._obj.send_command(self.command % block_ip)

class UnblockCommand(Command):

    command = 'undo ip route-static %s 255.255.255.255 NULL 0'

    def execute(self, ips):
        for block_ip in ips:
            print self.command % block_ip 
            logger.info('unblock_ip %s' % block_ip)
            out = self._obj.send_command(self.command % block_ip)

class ShowRoute(Command):

    command = 'display ip routing-table' 
    def execute(self, *args):
        logger.info(self.command)
        out = self._obj.send_command(self.command)
        return out



class sshClient(object):
    """The CLIENT class"""
    def __init__(self, login_info):
        ip, username, password = login_info
        self._ssh = ssh(login_info) 

    ## main = sys.modules['__main__']; getattr(main, cmd);
    ## ditc = globals() ;              dict[cmd]
    def switch(self, cmd, *args, **kargs):
        cmd = cmd.strip().upper()
        if cmd == "BLOCK":
            Switch.execute(BlockCommand(self._ssh), *args, **kargs)
        elif cmd == "UNBLOCK":
            Switch.execute(UnblockCommand(self._ssh), *args, **kargs)
        elif cmd == "ROUTE_TABLE": 
            return Switch.execute(ShowRoute(self._ssh), *args, **kargs)
        else:
            print "Argument 'BLOCK' or 'UNBLOCK' is required."


class ssh(object):
   
    PROMPT = r'\(\w+\)'
    SPROMPT = r'\[\w+\]'

    def __init__(self, login_info):
        ip, username, password = login_info
        self.ssh = pexpect.spawn('ssh -1  %s@%s' % (username, ip))
        self.ssh.logfile = open(ip, 'ab')
        if self.ssh.expect('password') == 0:
            self.ssh.sendline(password)
            if self.ssh.expect(self.PROMPT) == 0:
                logger.info('login success')
                self.send_command('system-view')

    def send_command(self, com):
        self.ssh.sendline(com)
        self.ssh.expect([self.PROMPT, self.SPROMPT]) 
        return self.ssh.before 
	


def get_info(filename='block_ip.json'):
    f = open(filename, 'rb')
    j = json.load(f)
    f.close()
    return ( 
            (j['ip'], j['username'], j['password']),
            j['block_ips'],
            j['command']
           )

def get_ssh():
    login_info, ips, _ = get_info()
    ssh = sshClient(login_info)
    return ssh


if __name__ == "__main__":
    login_info, ips, _ = get_info()
    ssh = sshClient(login_info)
    ssh.switch('BLOCK', ips)
    ssh.switch('UNBLOCK', ips, time=10)
