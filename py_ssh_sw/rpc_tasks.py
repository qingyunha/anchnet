from SimpleXMLRPCServer import SimpleXMLRPCServer
from threading import Timer


def unblock_ips(login_info, ips, delay):
    def f():
        ssh = sshClient(login_info)
        ssh.run('unblock', ips)
        ssh.terminate(force=True)
    t = Timer(time, f)
    t.start()


server = SimpleXMLRPCServer(("localhost", 8000))
print "Listening on port 8000..."
server.register_function(unblock_ips, "unblock_ips")
server.serve_forever()
