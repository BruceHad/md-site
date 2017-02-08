import configparser, os
from ftplib import FTP

def upload_dir(ftp, src_dir):
	os.chdir(src_dir)
	for f in os.listdir():
		print(f)
		if os.path.isfile(f):
			# remote_mod_date = ftp.sendcmd('MDTM ' + f)
			# local_mod_date
			fh = open(f, 'rb')
			ftp.storbinary('STOR %s' % f, fh)
			fh.close()
		elif os.path.isdir(f):
			if f not in ftp.nlst(): 
				ftp.mkd(f)
			ftp.cwd(f)
			upload_dir(ftp, f)
	ftp.cwd('..')
	os.chdir('..')

# Read in config data
config = configparser.ConfigParser()
config.read('config.ini')
user = config['FTP']['user']
host = config['FTP']['host']
pw = config['FTP']['pw']
src_dir = config['blog']['live']
target_dir = config['blog']['target']

# Connect
ftp = FTP(host, user, pw)
ftp.cwd(target_dir)

# Update
upload_dir(ftp, src_dir)
ftp.quit()