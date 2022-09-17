# import dataclasses
import datetime
import glob
import hashlib
import os
import pathlib
import stat
import sys
try:
    # Only for Windows
    import win32security
except ModuleNotFoundError:
    pass

# @dataclasses.dataclass
# class Names:
#     unames: dict
#     gnames: dict

def help(args):
    put_message(f'fileinfo - List File attributes')
    put_message(f'[VERSION]')
    put_message(f'  {version()}')
    put_message(f'[COPYRIGHT]')
    put_message(f'  {copyright()}')
    put_message(f'[LICENSE]')
    put_message(f'  {license()}')
    put_message(f'[SYNOPSIS]')
    put_message(f'  {args[0]} [ File | Directory ]...')

def put_message(message):
    print(message)

def version():
    #return f'1.0.0 (2022/08/28) for Python 3.x or later; (Tested for Python 3.9.1 on MacBook Pro)'
    # return f'1.0.1 (2022/08/29) for Python 3.x or later; (Tested for Python 3.7.4 on Windows 10 Pro 21H1)'
    # return f'1.0.2 (2022/08/29) for Python 3.x or later; (Tested for Python 3.7.4 on Windows 10 Pro 21H1 and for Python 3.9.1 on MacBook Pro)'
    # return f'1.0.3 (2022/08/30) for Python 3.x or later; (Tested for Python 3.6.8 on Redhat Enterprise Linux 8.2, Python 3.7.4 on Windows 10 Pro 21H1 and for Python 3.9.1 on MacBook Pro)'
    return f'1.0.4 (2022/09/17) for Python 3.x or later; (Tested for Python 3.6.8 on Redhat Enterprise Linux 8.2, Python 3.7.4 on Windows 10 Pro 21H1 and for Python 3.9.1 on MacBook Pro; Source indentation by 4 spaces.)'

def copyright():
    return f'Copyright© 2022, kimura.shinichi@ieee.org'

def license():
    return f'Licensed by Apache License 2.0( {apache_license_url()} ) or later.'

def apache_license_url():
    return f'https://www.apache.org/licenses/LICENSE-2.0'

def main(args) -> int:
    if len(args) < 2:
        help(args)
        return 1

    # names = Names(unames={}, gnames={})
    names = {'unames':{}, 'gnames':{}}
    for f in args[1:]:
        dir_stat_invisibly(f, names)
        show(f, names)
    return 0

def dir_stat_invisibly(file, names):
    dir = os.path.dirname(file)
    if '' == dir:
        stat_str('.', names)
    else:
        stat_str(dir, names)

def show(file, names):
    put_fileinfo(stat_str(file, names))

    file_path = pathlib.Path(file)
    if os.path.isdir(file_path):
        # Do not follow any symbolic links.
        if os.path.islink(file_path):
            return

        dir = file_path
        try:
            # Show about all the children of dir.
            children = dir.glob('*')

            for child in children:
                try:
                    child_path = f'{child}'
                    show(child_path, names)
                except PermissionError:
                    put_fileinfo(f'(Skipping {child_path})')
        except PermissionError:
            put_fileinfo(f'(Skipping children of {dir})')

def put_fileinfo(fileinfo_str):
    print(fileinfo_str)

def stat_str(file, names):
    s = os.stat(file, follow_symlinks=False)
    # s.st_mode - protection bits,
    # s.st_ino - inode number,
    # s.st_dev - device,
    # s.st_nlink - number of hard links,
    # s.st_uid - user id of owner,
    # s.st_gid - group id of owner,
    # s.st_size - size of file, in bytes,
    # s.st_atime - time of most recent access,
    # s.st_mtime - time of most recent content modification,
    # s.st_ctime - platform dependent; time of most recent metadata change on Unix, or the time of creation on Windows)

    mode = stat.filemode(s.st_mode)
    nlink = s.st_nlink
    uid = s.st_uid
    path = pathlib.Path(file)
    # uname = get_uname(uid, path, names.unames)
    uname = get_uname(uid, path, names['unames'])
    gid = s.st_gid
    gname = get_gname(gid, path, names['gnames'])
    size = s.st_size
    hash = get_hash(file, mode)
    mtime = as_Ymd_HMS(s.st_mtime)
    link = get_link_symbol(path)
    return f'{mode} {nlink} {uname}({uid}):{gname}({gid}) {size} {hash} {mtime} {path}{link}'

def get_uname(uid, path, unames):
    return get_xname(uid, (lambda: get_owner(path)), unames)

def get_owner(path):
    try:
        xname = path.owner()
    except KeyError:
        xname = '(missing)'
    except NotImplementedError:
        # Try for Windows.
        try:
            sd = win32security.GetFileSecurity(str(path), win32security.OWNER_SECURITY_INFORMATION)
            owner_sid = sd.GetSecurityDescriptorOwner()
            name, domain, type = win32security.LookupAccountSid(None, owner_sid)
            xname = name
        except Exception as e:
            raise e
    return xname

def get_gname(gid, path, gnames):
    return get_xname(gid, (lambda: get_group(path)), gnames)

def get_group(path):
    try:
        xname = path.group()
    except KeyError:
        xname = '(missing)'
    except NotImplementedError:
        # Try for Windows.
        try:
            sd = win32security.GetFileSecurity(str(path), win32security.OWNER_SECURITY_INFORMATION)
            group_sid = sd.GetSecurityDescriptorGroup()
            if group_sid is not None:
                name, domain, type = win32security.LookupAccountSid(None, group_sid)
                xname = name
            else:
                xname = None
        except Exception as e:
            raise e
    return xname

def get_xname(xid, fun, xnames):
    if xid in xnames:
        xname = xnames[xid]
    else:
        try:
            xname = fun()
        except KeyError:
            xname = '(missing)'
        except NotImplementedError:
            xname = '(not-implemented)'
        if xname is not None:
            xnames[xid] = xname
    return xname

def get_hash(file, mode):
    return f'SHA256:{sha256(file, mode)}'

def get_link_symbol(path):
    if os.path.islink(path):
        try:
            link = f' -> {os.readlink(path)}'
        except FileNotFoundError:
            link = f' -> (No such file or directory)'
    else:
        link = ''
    return link

def as_Ymd_HMS(timestamp):
    dt = datetime_of(timestamp)
    return dt.strftime('%Y/%m/%d %H:%M:%S')

def datetime_of(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)

def sha256(file, mode):
    if '-' == mode[0]:
        return sha256_hex(file)
    elif 'd' == mode[0]:
        return f'directory'
    elif 'D' == mode[0]:
        return f'Door(Solaris)'
    elif 'b' == mode[0]:
        return f'block-special'
    elif 'c' == mode[0]:
        return f'character-special'
    elif 'C' == mode[0]:
        return f'Contiguous-data' # high performance ("contiguous data") file
    elif 'l' == mode[0]:
        return f'symbolic-link'
    elif 'M' == mode[0]:
        return f'Migrated' # off-line ("migrated") file (Cray DMF)
    elif 'n' == mode[0]:
        return f'network special' # (HP-UX)
    elif 's' == mode[0]:
        return f'socket'
    elif 'P' == mode[0]:
        return f'FIFO'
    elif 'p' == mode[0]:
        return f'FIFO'
    elif '?' == mode[0]:
        return f'some-other-file-type'
    else:
        raise TypeError(f'{mode[0]}: Unknown mode prefix of file: {file}')

def sha256_hex(file):
    m = hashlib.sha256()
    with open(file, 'rb') as f:
        try:
            bytes = f.read()
        except OSError as e:
            return f'(unreadable)'
        m.update(bytes)
    hex = m.hexdigest()
    return hex

main(sys.argv)
