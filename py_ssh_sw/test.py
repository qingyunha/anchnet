import web_ssh
import time
import unittest
import os,subprocess

class WebsshTest(unittest.TestCase):


    def setUp(self):
        self.app = web_ssh.app.test_client()

    def tearDown(self):
        pass


    def test_index_page(self):
        r = self.app.get('/')
        assert 'block' in r.data

    def test_block_ips(self):
        r = self.app.post('/block', data={'ip': '192.168.106.252', 'username': 'tao', 
                                  'password' : '123', 'block_ips': '1.1.1.1 2.2.2.2'})
        assert '2.2.2.2' in  r.data

    def test_ontime_unblock_ips(self):
        r = self.app.post('/block', data={'ip': '192.168.106.252', 'username': 'tao', 
                                  'password' : '123', 'block_ips': '1.1.1.1 2.2.2.2'})
        assert '2.2.2.2' in  r.data
        

        r = self.app.post('/unblock', data={'ip': '192.168.106.252', 'username': 'tao', 
                                  'password' : '123', 'block_ips': '1.1.1.1 2.2.2.2', 'time':'1'})
        time.sleep(3)
        
        print 'tail -n 2 comm_ssh.log'
        s = subprocess.check_output('tail -n 2 comm_ssh.log', shell=True)
        
        print s

        assert 'undo ip route-static 1.1.1.1' in  s
        assert 'undo ip route-static 2.2.2.2' in  s




    def test_limit_speed(self):
        r = self.app.post('/limit_speed', data={'ip': '192.168.106.252', 'username': 'tao',
                                'password' : '123', 'interface': '0/0/2', 'policy':'15M'})
        assert 'traffic-policy 15M inbound' in r.data

    def test_unlimit_speed(self):
        r = self.app.post('/unlimit_speed', data={'ip': '192.168.106.252', 'username': 'tao',
                                'password' : '123', 'interface': '0/0/2', })
        assert 'traffic-policy' not in r.data

if __name__ == '__main__':
    unittest.main()
