import os
from ftplib import FTP


def connect(ftphost, ftpuser, ftppw):
    return FTP(ftphost, ftpuser, ftppw)


def quit(ftp):
    ftp.quit


def upload_file(ftp, file_path):
    """ Upload a single file """
    # print(ftp.pwd(), os.getcwd(), file_path)
    fh = open(file_path, 'rb')
    ftp.storbinary('STOR %s' % file_path, fh)
    fh.close()


def upload_dir(ftp, src_dir, target_dir=None):
    """ Recusively upload the contents of dr """
    if target_dir:
        if target_dir not in ftp.nlst():
            make_directory(ftp, target_dir)
        ftp.cwd(target_dir)
    os.chdir(src_dir)
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


# def upload_multiple_files(ftp, fls):
#     """ Upload all file in fls """
#     for f in fls:
#         upload_file(ftp, f)


# def upload_multiple_drs(drs):
#     """ Upload multiple directories """
#     # Connect
#     ftp = FTP(FTPHOST, FTPUSER, FTPPW)
#     ftp.cwd(TARGET_DIR)
#     for dr in drs:
#         upload_dir(ftp, dr)
#     ftp.quit()


def make_directory(ftp, dr):
    print(dr)
    iwd = ftp.pwd()
    for d in dr.split("/"):
        print(ftp.pwd())
        print(d)
        if d not in ftp.nlst():
            ftp.mkd(d)
            ftp.cwd(d)
        else:
            ftp.cwd(d)
    ftp.cwd(iwd)


if __name__ == "__main__":
    pass
