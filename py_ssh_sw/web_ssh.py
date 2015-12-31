from flask import Flask, request, render_template
from pexpect_ssh import sshClient 


app = Flask(__name__)

def get_ssh(request, clients={}):
    login_info = (request.form['ip'], request.form['username'], 
                                      request.form['password'])
    if login_info[0] in clients:
        ssh = clients[login_info[0]]
    else:
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
    ssh.switch('BLOCK', ips)
    out = ssh.switch('ROUTE_TABLE') 
    return '<pre>' + out + '<pre>' 


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
        ssh.switch('UNBLOCK', ips, time=time)
        return '%d later' % time
    else:
        ssh.switch('UNBLOCK', ips)

    out = ssh.switch('ROUTE_TABLE') 
    return '<pre>' + out + '<pre>' 



@app.route("/route_table", methods=['GET', 'POST']) 
def show_route():
    if request.method == "GET":
        return  render_template('route_table.html') 
    else:
        ssh = get_ssh(request)
        out = ssh.switch('ROUTE_TABLE') 
        return '<pre>' + out + '<pre>' 
        

if __name__ == "__main__":
    app.run(host='0.0.0.0',  debug=True)
