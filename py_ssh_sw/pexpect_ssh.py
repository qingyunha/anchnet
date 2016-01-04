import pexpect
import logging, sys
import threading, time
import json

logger = logging.getLogger('comm_ssh')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('comm_ssh.log')
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

    command = ''

    def __init__(self, obj):
        self._obj = obj

    def execute(self):
        raise NotImplementedError

    def __str__(self):
        return str(self.command)

class BlockCommand(Command):

    command = 'ip route-static %s 255.255.255.255 NULL 0'

    def execute(self, ips):
        for block_ip in ips:
            logger.info('block_ip %s' % block_ip)
            out = self._obj.send_command(self.command % block_ip)

class UnblockCommand(Command):

    command = 'undo ip route-static %s 255.255.255.255 NULL 0'

    def execute(self, ips):
        for block_ip in ips:
            logger.info('unblock_ip %s' % block_ip)
            out = self._obj.send_command(self.command % block_ip)

class Route_tableCommand(Command):

    command = 'display ip routing-table' 
    def execute(self, *args):
        logger.info(self.command)
        out = self._obj.send_command(self.command)
        return out[1]

class Limit_speedCommand(Command):

    commands = ['traffic classifier {name} ',
                'if-match any',
                'quit',
                'traffic behavior {name}',
                'car cir {speed} cbs 655360 pbs 1000000',
                'quit',
                'traffic policy {name}',
                'classifier {name} behavior {name}',
                'quit',
                'interface Ethernet {interface}',
                'traffic-policy {name} inbound',
                'quit']

    commands = [ 'interface Ethernet {interface}',
                'traffic-policy {name} inbound',
                'display this']

    def execute(self, interface, policy):

        infos = {'name': policy, 
                'interface': interface, 
                }

        for cmd in self.commands:
            cmd = cmd.format(**infos)
            logger.info(cmd)
            r, s = self._obj.send_command(cmd)
            if r < 0 :
                logger.error('execute "%s" failed: %s' % (cmd,s))
                break
        self._obj.send_command('quit')
        return s

class Undo_limit_speedCommand(Command):
    commands = [ 'interface Ethernet {interface}',
                'undo traffic-policy inbound',
                'display this']

    def execute(self, interface):

        infos = { 
                'interface': interface, 
                }

        for cmd in self.commands:
            cmd = cmd.format(**infos)
            logger.info(cmd)
            r, s = self._obj.send_command(cmd)
            if r < 0 :
                logger.error('execute "%s" failed: %s' % (cmd,s))
                break
        self._obj.send_command('quit')
        return s



class Interface_policyCommand(Command):
    command = 'display traffic policy interface Ethernet {}'

    def execute(self, interface=None):
       
        cmd = self.command.format(interface)
        logger.info(cmd)
        r, s = self._obj.send_command(cmd)
        if r < 0 :
            logger.error('execute "%s" failed: %s' % (cmd,s))
        else:
            return s


class sshClient(object):
    """The CLIENT class"""
    def __init__(self, login_info):
        ip, username, password = login_info
        self._ssh = ssh(login_info) 
        self.commands = globals()

    def switch(self, cmd, *args, **kargs):
        cmd = cmd.strip().upper()
        if cmd == "BLOCK":
            Switch.execute(BlockCommand(self._ssh), *args, **kargs)
        elif cmd == "UNBLOCK":
            Switch.execute(UnblockCommand(self._ssh), *args, **kargs)
        elif cmd == "ROUTE_TABLE": 
            return Switch.execute(Route_tableCommand(self._ssh), *args, **kargs)
        else:
            print "Argument 'BLOCK' or 'UNBLOCK' is required."


    ## main = sys.modules['__main__']; getattr(main, cmd);
    ## ditc = globals() ;              dict[cmd]
    def run(self, cmd, *args, **kargs):
        cmd = cmd.strip().capitalize()
        commd  = self.commands.get(cmd + 'Command') 
        if commd:
            return Switch.execute(commd(self._ssh), *args, **kargs)
        else:
            print 'No such command:', cmd




class ssh(object):
   
    ERROR = 'Error'
    PROMPT = r'<\S+\>'
    SPROMPT = r'\[\S+\]'

    def __init__(self, login_info):
        try:
            ip, username, password = login_info
            self.ssh = pexpect.spawn('ssh -1  %s@%s' % (username, ip))
            self.ssh.logfile = open(ip, 'ab')
            self.ssh.expect('password')
            self.ssh.sendline(password)
            self.ssh.expect(self.PROMPT)
            logger.info('login success')
            self.send_command('system-view')
        except Exception,e:
            logger.info('login failed')
            raise e

    def send_command(self, com):
        self.ssh.sendline(com)
        try:
            index = self.ssh.expect([self.ERROR ,self.SPROMPT, self.PROMPT]) 
            if index == 0:
                self.ssh.expect([self.SPROMPT, self.PROMPT]) 
                return (-1 , self.ssh.before)
            else:
                return (1, self.ssh.before) 
        except:
            return(-1, 'failed')
	

    def isalive(self):
        r, s = self.send_command('')
        return True if r else False


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
    #ssh.switch('BLOCK', ips)
    #ssh.run('unBLOCK', ips)
    print ssh.run('limit_speed', '0/0/2', '15M')
    print ssh.run('interface_policy', '0/0/2')
    #ssh.switch('UNBLOCK', ips, time=9)
