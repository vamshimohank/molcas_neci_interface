import errno
import os.path

import paramiko

class SFTPHelper(object):
    import errno
    import os.path
    import paramiko


    def connect(self, hostname, **ssh_kwargs):
        """Create a ssh client and a sftp client

        **ssh_kwargs are passed directly to paramiko.SSHClient.connect()
        """

        self.ssh_config_file = os.path.expanduser("~/.ssh/config")
        #print(self.ssh_config_file)
        self.ssh_config = paramiko.SSHConfig()
        if os.path.exists(self.ssh_config_file):
            with open(self.ssh_config_file) as f:
                self.ssh_config.parse(f)
        self.user_config = self.ssh_config.lookup(hostname)
        #print(self.user_config)
        if 'proxycommand' in self.user_config:
            ssh_kwargs['sock'] = paramiko.ProxyCommand(self.user_config['proxycommand'])
        #print(ssh_kwargs)

        self.sshclient = paramiko.SSHClient()
        self.sshclient.load_system_host_keys()
        self.sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #self.user_config = ssh_config.lookup(hostname)
        self.sshclient.connect(hostname, **ssh_kwargs)
        self.sftpclient = self.sshclient.open_sftp()

    def remove_directory(self, path):
        """Remove remote directory that may contain files.
        It does not support directories that contain subdirectories
        """
        if self.exists(path):
            for filename in self.sftpclient.listdir(path):
                filepath = os.path.join(path, filename)
                self.sftpclient.remove(filepath)
            self.sftpclient.rmdir(path)

    def put_directory(self, localdir, remotedir):
        """Put a directory of files on the remote server
        Create the remote directory if it does not exist
        Does not support directories that contain subdirectories
        Return the number of files transferred
        """
        if not self.exists(remotedir):
            self.sftpclient.mkdir(remotedir)
        count = 0
        for filename in os.listdir(localdir):
            self.sftpclient.put(
                os.path.join(localdir, filename),
                os.path.join(remotedir, filename))
            count += 1
        return count

    def exists(self, path):
        """Return True if the remote path exists
        """
        try:
            self.sftpclient.stat(path)
        except IOError as e:
            if e.errno == errno.ENOENT:
                return False
            raise
        else:
            return True
