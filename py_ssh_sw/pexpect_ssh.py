import pexpect
import logging, sys
from threading import Timer
import time
import json
from datetime import datetime, timedelta
from sched import scheduler 


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
#logger.addHandler(ch)


class Switch(object):
    """The INVOKER class"""
    @classmethod
    def execute(cls, command, *args, **kwargs):
        '''
        if 'time' in kwargs:
            delay = kwargs['time']
            print 'sleep %d' % delay
            t = Timer(delay, command.execute, args)
            t.start()
        '''
        return command.execute(*args, **kwargs)

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
            out = self._obj.send_command(self.command % block_ip)



##
## for job missing, can add a event listener
## https://apscheduler.readthedocs.org/en/latest/modules/events.html#module-apscheduler.events
##
def unblock_ips_task(login_info, ips):
    ssh = sshClient(login_info)
    ssh.run('unblock', ips)
    ssh._ssh.ssh.terminate(force=True)


class UnblockCommand(Command):

    command = 'undo ip route-static %s 255.255.255.255'

    def execute(self, ips, delay=None):
        if delay is not None:
            delta = timedelta(seconds=delay)
            run_date = datetime.now() + delta
            print "tast run at ", run_date
            args = (self._obj.login_info, ips)
            scheduler.add_job(unblock_ips_task, 'date', args, run_date=run_date)
        else:
            for block_ip in ips:
                out = self._obj.send_command(self.command % block_ip)

class Route_tableCommand(Command):

    command = 'display ip routing-table' 

    def execute(self):
        s = self._obj.send_command(self.command)
        return s 

class Config_includeCommand(Command):

    command = 'display current-configuration | include %s'
    def execute(self,ip):
        self.command = self.command % ip
        s = self._obj.send_command(self.command)
        return s 



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
            s = self._obj.send_command(cmd)
            if s == '' :
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
            s = self._obj.send_command(cmd)
            if s == '' :
                break
        self._obj.send_command('quit')
        return s



class Interface_policyCommand(Command):
    command = 'display traffic policy interface Ethernet {}'

    def execute(self, interface=None):
       
        cmd = self.command.format(interface)
        s = self._obj.send_command(cmd)
        return s


class sshClient(object):
    """The CLIENT class"""
    def __init__(self, login_info):
        ip, username, password = login_info
        self._ssh = Ssh(login_info) 
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




class Ssh(object):
   
    ERROR = 'Error'
    PROMPT = r'<\S+\>'
    SPROMPT = r'\[\S+\]'

    ssh_line = 'ssh -o StrictHostKeyChecking=no %s@%s'
    def __init__(self, login_info):
        self.login_info = login_info
        try:
            ip, username, password = login_info
            self.ssh = pexpect.spawn('ssh -1  %s@%s' % (username, ip))
            self.ssh.logfile = open(ip, 'ab')
            self.ssh.expect('password')
            self.ssh.sendline(password)
            self.ssh.expect(self.PROMPT)
            logger.info('%s login success' % ip)
            self.send_command('system-view')
        except Exception,e:
            logger.info('login failed')
            raise e

    def send_command(self, com):
        self.ssh.sendline(com)
        logger.info(com)
        try:
            index = self.ssh.expect([self.ERROR ,self.SPROMPT, self.PROMPT]) 
            if index == 0:
                logger.error('execute "%s" error' % (com))
                self.ssh.expect([self.SPROMPT, self.PROMPT]) 
                return ''
            else:
                return self.ssh.before

        except pexpect.TIMEOUT:
            logger.error('execute "%s" timeout' % (com))
        except pexpect.EOF:
            logger.error('execute "%s" failed' % (com))
	
        return ''

    def isalive(self):
        r = self.send_command('')
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
    login_info = ('58.215.139.136', 'hjh_test', 'www.51idc.com')
    ips = ['58.215.139.12']
    login_info, ips, _ = get_info()
    ssh = sshClient(login_info)
    #print ssh.run('route_table')
    #print ssh.run('config_include', '192.168.')
    ssh.switch('BLOCK', ips)
    #ssh.run('unBLOCK', ips)
    #print ssh.run('limit_speed', '0/0/2', '15M')
    #print ssh.run('interface_policy', '0/0/2')
    ssh.switch('UNBLOCK', ips, delay=f)
    time.sleep(5)
