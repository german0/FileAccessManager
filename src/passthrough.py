#!/usr/bin/env python

from __future__ import with_statement

import os
import stat
import sys
import errno
import time
import send_mail
import config
import json

from fuse import FUSE, FuseOSError, Operations, fuse_get_context


class Passthrough(Operations):
    def __init__(self, root,idroot):
        self.root = root
        self.idroot = idroot
    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def getusers(self, lines):
        users = {}
        for line in lines:
            user, contact, perms = line.split(':')
            users[user] = (contact,perms)
        return users

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        full_path = self._full_path(path)
        fd = open("users.reg","r")
        data = json.load(fd)
        fd.close()
        uid,gui,pid = fuse_get_context()
        if (str(uid) not in data):
            send_mail.redirect(uid)
        else:
            if not os.access(full_path, mode):
                raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))


    def readdir(self, path, fh):
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        return os.symlink(name, self._full_path(target))

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        full_path = self._full_path(path)
        uid, gid, pid = fuse_get_context()
        fd = open("users.reg","r")
        users = json.load(fd)
        fd.close()
        if (uid != self.idroot):
            contact = users[str(uid)]
            fd = open("activation.json","r")
            data = json.load(fd)
            fd.close()
            info = data[str(contact)]
            if str(full_path) not in info["files"]:
                send_mail.send_email(str(contact),full_path)
                raise FuseOSError(errno.EACCES)
            else:
                return os.open(full_path,flags)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        uid, gid, pid = fuse_get_context()
        send_mail.add_file_access(uid,full_path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


def main(root):
    mountpoint = 'mountpoint'
    curr_dir = os.getcwd()
    if (os.path.exists(mountpoint)):
        print("Creating /mountpoint directory. Done.")
        os.rmdir(mountpoint)
        os.mkdir(mountpoint)
    else:
        print("Creating /mountpoint directory. Done.")
        os.mkdir(mountpoint)
    
    st = os.stat(mountpoint)

    #creating users register
    #fd = open("users.reg","w")
    rootid = os.getuid()
    #user = {}
    #user[rootid] = config.EMAIL_ADDRESS
    #json.dump(user,fd)
    #fd.close()
    #send_mail.start_log()
    FUSE(Passthrough(root,rootid), mountpoint, nothreads=True, foreground=True, **{'allow_other':True})

if __name__ == '__main__':
    #main(sys.argv[1])
    main("../root")