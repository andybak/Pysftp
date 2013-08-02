"""Friendly Python SFTP interface.

pysftp is forked with permission of ssh.py, originally authored by
Zeth @ http://commandline.org.uk/python/sftp-python-really-simple-ssh/

requires:
paramiko - http://www.lag.net/paramiko/
  requires:
  pycrypto - http://www.dlitz.net/software/pycrypto/

License: BSD  (see http://code.google.com/p/pysftp/source/browse/trunk/LICENSE.txt)
"""

import os
import tempfile
import paramiko

from contextlib import contextmanager

__version__ = "$Rev$"
class Connection(object):
    """Connects and logs into the specified hostname. 
    Arguments that are not given are guessed from the environment.
        host             - The Hostname of the remote machine.
        username         - Your username at the remote machine.(None)
        private_key      - Your private key file.(None)
        password         - Your password at the remote machine.(None)
        port             - The SSH port of the remote machine.(22)
        private_key_pass - password to use if your private_key is encrypted(None)
        log              - log connection/handshake details (False)
    returns a connection to the requested machine
    
    srv = pysftp.Connection('example.com')
    """ 

    def __init__(self,
                 host,
                 username = None,
                 private_key = None,
                 password = None,
                 port = 22,
                 private_key_pass = None,
                 log = False,
                 ):
        self._sftp_live = False
        self._sftp = None
        if not username:
            username = os.environ['LOGNAME']


        if log:
            # Log to a temporary file.
            templog = tempfile.mkstemp('.txt', 'ssh-')[1]
            paramiko.util.log_to_file(templog)

        # Begin the SSH transport.
        self._transport = paramiko.Transport((host, port))
        self._tranport_live = True
        self._ssh = paramiko.SSHClient()
        self._ssh.load_system_host_keys()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Authenticate the transport. prefer password if given
        if password:
            # Using Password.
            self._transport.connect(
                username=username,
                password=password
            )
            self._ssh.connect(
                host,
                username=username,
                password=password,
                port=port
            ) 
        else:
            # Use Private Key.
            if not private_key:
                # Try to use default key.
                if os.path.exists(os.path.expanduser('~/.ssh/id_rsa')):
                    private_key = '~/.ssh/id_rsa'
                elif os.path.exists(os.path.expanduser('~/.ssh/id_dsa')):
                    private_key = '~/.ssh/id_dsa'
                else:
                    raise TypeError, "You have not specified a password or key."

            private_key_file = os.path.expanduser(private_key)
            try:  #try rsa
                xSx_key = paramiko.RSAKey.from_private_key_file(private_key_file,private_key_pass)
            except paramiko.SSHException:   #if it fails, try dss
                xSx_key = paramiko.DSSKey.from_private_key_file(private_key_file,password=private_key_pass)
            self._transport.connect(username = username, pkey = xSx_key)
            self._ssh.connect(host, username=username,
                pkey=xSx_key, port=port) 

    
    def _sftp_connect(self):
        """Establish the SFTP connection."""
        if not self._sftp_live:
            self._sftp = paramiko.SFTPClient.from_transport(self._transport)
            self._sftp_live = True
    
    @property
    def client(self):
        """Expose paramiko Channel object for advanced use."""
        return self._ssh
    
    @property
    def sftp_client(self):
        """Expose paramiko SFTPClient object for advanced use."""
        self._sftp_connect()
        return self._sftp

    @contextmanager
    def cd(self, remote_dir):
        """Context manager to provide with changed directory."""
        old_dir = self.getcwd()
        try:
            self.chdir(remote_dir)
            yield
        finally:
            self.chdir(old_dir)

    def get(self, remotepath, localpath = None):
        """Copies a file between the remote host and the local host."""
        if not localpath:
            localpath = os.path.split(remotepath)[1]
        self._sftp_connect()
        self._sftp.get(remotepath, localpath)
        
    @contextmanager
    def open(self, remotepath, mode='r'):
        """Copies a remote file."""
        self._sftp_connect()
        remote_file = self._sftp.open(remotepath, mode)
        try:
            yield remote_file
        finally:
            remote_file.close()

    def put(self, localpath, remotepath = None):
        """Copies a file between the local host and the remote host."""
        if not remotepath:
            remotepath = os.path.split(localpath)[1]
        self._sftp_connect()
        self._sftp.put(localpath, remotepath)
        
    def exists(self, path):
        self._sftp_connect()
        try:
            self._sftp.stat(path)
        except IOError, e:
            if e[0] == 2:
                return False
            raise
        else:
            return True

    def size_match(self, remotepath, localpath = None):
        if not localpath:
            localpath = os.path.split(remotepath)[1]
        local_size = os.stat(localpath).st_size
        self._sftp_connect()
        try:
            remote_size = self._sftp.stat(remotepath).st_size
            if local_size == remote_size:
                return True
            else:
                return False
        except IOError, e:
            if e[0] == 2: 
                return False
            raise
        else:
            raise
        
    def mkdir(self, remotepath):
        self._sftp_connect()
        self._sftp.mkdir(remotepath)

    def mkdir_all(self, remotepath):
        self._sftp_connect()
        if self.exists(remotepath):
            return
        else:
            try:
                self.mkdir(remotepath)
            except IOError:
                self.mkdir_all(posixpath.split(remotepath)[0])
        
    def mkdir_put(self, localpath, remotepath = None):
        if not remotepath:
            remotepath = posixpath.split(localpath)[1]
        self._sftp_connect()
        self.mkdir_all(posixpath.split(remotepath)[0])
        self._sftp.put(localpath, remotepath)

    def execute(self, command):
        """Execute the given commands on a remote machine."""
        channel = self._transport.open_session()
        channel.exec_command(command)
        output = channel.makefile('rb', -1).readlines()
        if output:
            return output
        else:
            return channel.makefile_stderr('rb', -1).readlines()

    def chdir(self, path):
        """change the current working directory on the remote"""
        self._sftp_connect()
        self._sftp.chdir(path)
        
    def getcwd(self):
        """return the current working directory on the remote"""
        self._sftp_connect()
        return self._sftp.getcwd()
        
    def listdir(self, path='.'):
        """return a list of files for the given path"""
        self._sftp_connect()
        return self._sftp.listdir(path)
        
    def close(self):
        """Closes the connection and cleans up."""
        # Close SFTP Connection.
        if self._sftp_live:
            self._sftp.close()
            self._sftp_live = False
        # Close the SSH Transport.
        if self._tranport_live:
            self._transport.close()
            self._tranport_live = False

    def __del__(self):
        """Attempt to clean up if not explicitly closed."""
        self.close()

def main():
    """Little test when called directly."""
    # Set these to your own details.
    myssh = Connection('example.com')
    myssh.put('ssh.py')
    myssh.close()

# start the ball rolling.
if __name__ == "__main__":
    main()