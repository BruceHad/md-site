import os
import configparser
from ftplib import FTP

# Read in config data
# config = configparser.ConfigParser()
# config.read('config_live.ini')
# SRC_PATH = config['blog']['src']
# LIVE_PATH = config['blog']['live']
# TARGET_DIR = config['blog']['target']
# TEMPLATE_PATH = config['blog']['templates']
# FTPUSER = config['FTP']['user']
# FTPHOST = config['FTP']['host']
# FTPPW = config['FTP']['pw']


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


# def upload_multiple_drs(drs):
#     """ Upload multiple directories """
#     # Connect
#     ftp = FTP(FTPHOST, FTPUSER, FTPPW)
#     ftp.cwd(TARGET_DIR)
#     for dr in drs:
#         upload_dir(ftp, dr)
#     ftp.quit()

def make_directory(ftp, dr):
    iwd = ftp.pwd()
    for d in dr.split("/"):
        if d not in ftp.nlst():
            ftp.mkd(d)
            ftp.cwd(d)
        else:
            ftp.cwd(d)
    ftp.cwd(iwd)


def upload_site(src):
    """ Upload full contents of site rooted at src """
    ftp = FTP(FTPHOST, FTPUSER, FTPPW)
    # print(ftp.pwd(), ftp.nlst(), TARGET_DIR)
    make_directory(ftp, TARGET_DIR)
    ftp.cwd(TARGET_DIR)
    upload_dir(ftp, src)
    ftp.quit()


def upload_posts(src, posts):
    """ Upload only the new/changed posts. """
    ftp = FTP(FTPHOST, FTPUSER, FTPPW)
    # print(ftp.pwd(), ftp.nlst(), TARGET_DIR)
    for p in posts:
        src_dr = os.path.join(src, 'posts', p)
        post_dr = os.path.join(TARGET_DIR, 'posts', p)
        # print(src_dr, post_dr)
        make_directory(ftp, post_dr)
        ftp.cwd(post_dr)
        upload_dir(ftp, src_dr)
    ftp.quit()


def delete_posts(posts):
    """ Delete any old folder from server """
    ftp = FTP(FTPHOST, FTPUSER, FTPPW)
    root = os.path.join(TARGET_DIR, 'posts')
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
    ftp = FTP(FTPHOST, FTPUSER, FTPPW)
    # print(ftp.pwd(), ftp.nlst(), TARGET_DIR)
    ftp.cwd(TARGET_DIR)
    os.chdir(src)
    # src_file = os.path.join(src, 'index.html')
    upload_file(ftp, 'index.html')
    ftp.quit()


if __name__ == "__main__":
    pass
