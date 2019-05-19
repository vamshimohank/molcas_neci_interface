

import paramiko
import os

user_config_file = os.path.expanduser("~/.ssh/config")

ssh_config = paramiko.SSHConfig()

if os.path.exists(user_config_file):
    with open(user_config_file) as f:
        ssh_config.parse(f)

user_config = ssh_config.lookup('cobra')


cfg={'hostname': 'cobra', 'username': 'vkatukur', 'password': 'Attaya9*123'}

cfg['sock']=paramiko.ProxyCommand(user_config['proxycommand'])

client=paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(**cfg)


