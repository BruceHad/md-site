import configparser
import os, sys
from ftplib import FTP


# Read in config data
config = configparser.ConfigParser()
config.read('config.ini')
user = config['FTP']['user']
host = config['FTP']['host']
pw = config['FTP']['pw']
src_dir = config['blog']['live']
target_dir = config['blog']['target']


def upload_file(ftp, file_path):
    """ Upload a single file """
    # print(ftp.pwd(), file_path)
    fh = open(file_path, 'rb')
    ftp.storbinary('STOR %s' % file_path, fh)
    fh.close()


def upload_dir(ftp, dr):
    """ Recusively upload the contents of dr """
    os.chdir(dr)
    for f in os.listdir():
        if os.path.isfile(f):
            upload_file(ftp, f)
        elif os.path.isdir(f):
            if f not in ftp.nlst():
                ftp.mkd(f)
            ftp.cwd(f)
            upload_dir(ftp, f)
    ftp.cwd('..')
    os.chdir('..')


def upload_multiple_files(ftp, fls):
    """ Upload all file in fls """
    for f in fls:
        upload_file(ftp, f)


def upload_multiple_drs(drs):
    """ Upload multiple directories """
    # Connect
    ftp = FTP(host, user, pw)
    ftp.cwd(target_dir)
    for dr in drs:
        upload_dir(ftp, dr)
    ftp.quit()


def make_directory(ftp, dir):
    iwd = ftp.pwd()
    for d in dir.split('/'):
        if d not in ftp.nlst():
            ftp.mkd(d)
            ftp.cwd(d)
        else:
            ftp.cwd(d)
    ftp.cwd(iwd)


def upload_site(src):
    """ Upload full contents of site rooted at src """
    ftp = FTP(host, user, pw)
    # print(ftp.pwd(), ftp.nlst(), target_dir)
    make_directory(ftp, target_dir)
    ftp.cwd(target_dir)
    upload_dir(ftp, src)
    ftp.quit()


def upload_posts(src, posts):
    """ Upload only the new/changed posts. """
    ftp = FTP(host, user, pw)
    # print(ftp.pwd(), ftp.nlst(), target_dir)
    for p in posts:
        src_dr = os.path.join(src, 'posts', p)
        post_dr = os.path.join(target_dir, 'posts', p)
        # print(src_dr, post_dr)
        make_directory(ftp, post_dr)
        ftp.cwd(post_dr)
        upload_dir(ftp, src_dr)
    ftp.quit()


def delete_posts(posts):
    """ Delete any old folder from server """
    ftp = FTP(host, user, pw)
    root = os.path.join(target_dir, 'posts')
    ftp.cwd(root)
    for p in posts:
        if p in ftp.nlst():
            ftp.cwd(p)
            for f in ftp.nlst():
                if f not in ['.', '..']:
                    print(f)
                    print(ftp.delete(f))
            ftp.cwd('..')
            print(ftp.pwd())
            ftp.rmd(p)
    ftp.quit()


def upload_changed_index(src):
    ftp = FTP(host, user, pw)
    # print(ftp.pwd(), ftp.nlst(), target_dir)
    ftp.cwd(target_dir)
    os.chdir(src)
    # src_file = os.path.join(src, 'index.html')
    upload_file(ftp, 'index.html')
    ftp.quit()


if __name__ == "__main__":
    pass
