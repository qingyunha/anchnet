from flask import Flask, request, render_template
from pexpect_ssh import sshClient 


app = Flask(__name__)

def get_ssh(request, clients={}):
    login_info = (request.form['ip'], request.form['username'], 
                                      request.form['password'])
    if login_info[0] in clients:
        ssh = clients[login_info[0]]
        if ssh._ssh.isalive():
            return ssh
    ssh = sshClient(login_info)
    clients[login_info[0]] = ssh
    return ssh


@app.route("/")
def hello():
    return  render_template('index.html')

##  block ips
@app.route("/block", methods=['GET',])
def show_block():
    return  render_template('block.html')

@app.route("/block", methods=['POST'])
def block():
    ssh = get_ssh(request)
    ips = request.form['block_ips'].split()
    ssh.run('BLOCK', ips)
    #out = ssh.run('ROUTE_TABLE') 
    out = []
    for ip in ips:
        out.append(ssh.run('config_include',ip))
    return '<pre>' + '\n'.join(out) + '<pre>' 


## unblock ips
@app.route("/unblock", methods=['GET',])
def show_unblock():
    return  render_template('unblock.html')


@app.route("/unblock", methods=['POST'])
def unblock():
    ssh = get_ssh(request)
    ips = request.form['block_ips'].split()
    time = int(request.form['time'])
    if time:
        ssh.run('UNBLOCK', ips, time=time)
        return '%d later' % time
    else:
        ssh.run('UNBLOCK', ips)

    #out = ssh.run('ROUTE_TABLE') 
    out = []
    for ip in ips:
        out.append(ssh.run('config_include',ip))
    return '<pre>' + '\n'.join(out) + '<pre>' 
    return '<pre>' + out + '<pre>' 



@app.route("/route_table", methods=['GET', 'POST']) 
def show_route():
    if request.method == "GET":
        return  render_template('route_table.html') 
    else:
        ssh = get_ssh(request)
        out = ssh.run('ROUTE_TABLE') 
        return '<pre>' + out + '<pre>' 
        


@app.route("/limit_speed", methods=['GET', 'POST']) 
def limit_speed():
    if request.method == "GET":
        return  render_template('limit_speed.html') 
    else:
        ssh = get_ssh(request)
        policy = request.form['policy']
        interface = request.form['interface']
        out = ssh.run('limit_speed',interface, policy)
        #out = ssh.run('interface_policy', interface) 
        return '<pre>' + out + '<pre>' 


@app.route("/unlimit_speed", methods=['GET', 'POST']) 
def unlimit_speed():
    if request.method == "GET":
        return  render_template('unlimit_speed.html') 
    else:
        ssh = get_ssh(request)
        interface = request.form['interface']
        out = ssh.run('undo_limit_speed',interface)
        #out = ssh.run('interface_policy', interface) 
        return '<pre>' + out + '<pre>' 

if __name__ == "__main__":
    app.run(host='0.0.0.0',  debug=True)
