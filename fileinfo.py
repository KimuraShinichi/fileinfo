"""
Generates file information text list such as the output of UNIX/Linux ls -l.
"""
import datetime
import hashlib
import os
import pathlib
import platform
import stat
import sys

def only_for_windows():
    """Return if the platform.system() is 'Windows'."""
    return platform.system() == 'Windows'

if only_for_windows():
    import win32security

def fileinfo_help(args):
    """Show help message."""
    put_message(f'fileinfo - List File attributes')
    put_message(f'[VERSION]')
    put_message(f'  {fileinfo_version()}')
    put_message(f'[COPYRIGHT]')
    put_message(f'  {fileinfo_copyright()}')
    put_message(f'[LICENSE]')
    put_message(f'  {fileinfo_license()}')
    put_message(f'[SYNOPSIS]')
    put_message(f'  {args[0]} [ File | Directory ]...')

def put_message(message):
    """Puts the message text into the standard out."""
    print(message)

def fileinfo_version():
    """Returns the version message."""
    # return f'1.0.0 (2022/08/28) for Python 3.x or later; \
    # (Tested for Python 3.9.1 on MacBook Pro)'
    # return f'1.0.1 (2022/08/29) for Python 3.x or later; \
    # (Tested for Python 3.7.4 on Windows 10 Pro 21H1)'
    # return f'1.0.2 (2022/08/29) for Python 3.x or later; \
    # (Tested for Python 3.7.4 on Windows 10 Pro 21H1 and \
    # for Python 3.9.1 on MacBook Pro)'
    # return f'1.0.3 (2022/08/30) for Python 3.x or later; \
    # (Tested for Python 3.6.8 on Redhat Enterprise Linux 8.2, \
    # Python 3.7.4 on Windows 10 Pro 21H1 and for Python 3.9.1 on MacBook Pro)'
    # return f'1.0.4 (2022/09/17) for Python 3.x or later; '\
    #    + f'(Tested for Python 3.6.8 on Redhat Enterprise Linux 8.2, '\
    #    + f'Python 3.7.4 on Windows 10 Pro 21H1 and for Python 3.9.1 on MacBook Pro; '\
    #    + f'Source indentation by 4 spaces.)'
    return f'1.0.5 (2022/09/18) for Python 3.x or later; '\
        + f'(Tested for Python 3.6.8 on Redhat Enterprise Linux 8.2, '\
        + f'Python 3.7.4 on Windows 10 Pro 21H1 and for Python 3.9.1 on MacBook Pro; '\
        + f'Clean for PyLint[except 1 E0401].)'

def fileinfo_copyright():
    """Returns the copyright notification."""
    return f'Copyright© 2022, kimura.shinichi@ieee.org'

def fileinfo_license():
    """Returns the license notification."""
    return f'Licensed by Apache License 2.0( {apache_license_url()} ) or later.'

def apache_license_url():
    """Returns the URL of The Apache Software Licence 2.0."""
    return f'https://www.apache.org/licenses/LICENSE-2.0'

def main(args) -> int:
    """The main program entrance."""
    if len(args) < 2:
        fileinfo_help(args)
        return 1

    names = {'unames':{}, 'gnames':{}}
    for arg in args[1:]:
        dir_stat_invisibly(arg, names)
        show(arg, names)
    return 0

def dir_stat_invisibly(file, names):
    """
    Make the directory of the file or the current directory
    without showing fileinfo.
    """
    a_directory = os.path.dirname(file)
    if a_directory:
        stat_str(a_directory, names)
    else:
        stat_str('.', names)

def show(file, names):
    """Show the fileinfo of the file and / or its children."""
    put_fileinfo(stat_str(file, names))

    file_path = pathlib.Path(file)
    if os.path.isdir(file_path):
        # Do not follow any symbolic links.
        if os.path.islink(file_path):
            return

        a_directory = file_path
        try:
            # Show about all the children of a_directory.
            children = a_directory.glob('*')

            for child in children:
                try:
                    child_path = f'{child}'
                    show(child_path, names)
                except PermissionError:
                    put_fileinfo(f'(Skipping {child_path})')
        except PermissionError:
            put_fileinfo(f'(Skipping children of {a_directory})')

def put_fileinfo(fileinfo_str):
    """Put a file-info string to the standard out."""
    print(fileinfo_str)

def stat_str(file, names):
    """
    Get a text representation of the stat values of the file
    using dictionary pair names.
    """
    stat_info = os.stat(file, follow_symlinks=False)
    # stat_info.st_mode - protection bits,
    # stat_info.st_ino - inode number,
    # stat_info.st_dev - device,
    # stat_info.st_nlink - number of hard links,
    # stat_info.st_uid - user id of owner,
    # stat_info.st_gid - group id of owner,
    # stat_info.st_size - size of file, in bytes,
    # stat_info.st_atime - time of most recent access,
    # stat_info.st_mtime - time of most recent content modification,
    # stat_info.st_ctime - platform dependent; time of most recent metadata change \
    # on Unix, or the time of creation on Windows)

    mode = stat.filemode(stat_info.st_mode)
    nlink = stat_info.st_nlink
    uid = stat_info.st_uid
    path = pathlib.Path(file)
    # uname = get_uname(uid, path, names.unames)
    uname = get_uname(uid, path, names['unames'])
    gid = stat_info.st_gid
    gname = get_gname(gid, path, names['gnames'])
    size = stat_info.st_size
    a_hash = get_hash(file, mode)
    mtime = as_datetime_style(stat_info.st_mtime)
    link = get_link_symbol(path)
    return f'{mode} {nlink} {uname}({uid}):{gname}({gid}) {size} {a_hash} {mtime} {path}{link}'

def get_uname(uid, path, unames):
    """Get the name of uid of the path with a dictionary unames."""
    return get_xname(uid, (lambda: get_owner(path)), unames)

def get_owner(path):
    """Get owner of the path."""
    try:
        xname = path.owner()
    except KeyError:
        xname = '(missing)'
    except NotImplementedError:
        # Try for Windows.
        if only_for_windows():
            security_descriptor = win32security.GetFileSecurity(
                str(path),
                win32security.OWNER_SECURITY_INFORMATION
            )
            owner_sid = security_descriptor.GetSecurityDescriptorOwner()
            a_name, _, _ = win32security.LookupAccountSid(None, owner_sid)
            xname = a_name
        else:
            raise
    return xname

def get_gname(gid, path, gnames):
    """Get the name of gid group of the path with a dictionary gnames."""
    return get_xname(gid, (lambda: get_group(path)), gnames)

def get_group(path):
    """Get group of the path."""
    try:
        xname = path.group()
    except KeyError:
        xname = '(missing)'
    except NotImplementedError:
        if only_for_windows():
            security_descriptor = win32security.GetFileSecurity(
                str(path),
                win32security.OWNER_SECURITY_INFORMATION
            )
            group_sid = security_descriptor.GetSecurityDescriptorGroup()
            if group_sid is not None:
                a_name, _, _ = win32security.LookupAccountSid(None, group_sid)
                xname = a_name
            else:
                xname = None
        else:
            raise
    return xname

def get_xname(xid, fun, xnames):
    """
    Get somewhat-name of the xid using function fun
    and the xid-keyed dictionary xnames.
    """
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
    """Get a hash value of the file on its mode."""
    return f'SHA256:{sha256(file, mode)}'

def get_link_symbol(path):
    """Get a referring path of the symbolic link of that path."""
    if os.path.islink(path):
        try:
            link = f' -> {os.readlink(path)}'
        except FileNotFoundError:
            link = f' -> (No such file or directory)'
    else:
        link = ''
    return link

def as_datetime_style(timestamp):
    """Returns the text representation of the timestamp."""
    a_datetime = datetime_of(timestamp)
    return a_datetime.strftime('%Y/%m/%d %H:%M:%S')

def datetime_of(timestamp):
    """Returns the datetime of the timestamp."""
    return datetime.datetime.fromtimestamp(timestamp)

def sha256(file, mode):
    """
    Returns SHA-256 hash value hexadecimal text
    or some other text representation of the file
    which depends on its mode.
    """
    if mode[0] == '-':
        return sha256_hex(file)
    a_dict = {
        'd': 'directory',
        'D': 'Door(Solaris)',
        'b': 'block-special',
        'c': 'character-special',
        'C': 'Contiguous-data', # high performance ("contiguous data") file
        'l': 'symbolic-link',
        'M': 'Migrated', # off-line ("migrated") file (Cray DMF)
        'n': 'network special', # (HP-UX)
        's': 'socket',
        'P': 'FIFO',
        'p': 'FIFO',
        '?': 'some-other-file-type'
    }
    if mode[0] in a_dict.keys():
        return a_dict[mode[0]]
    raise TypeError(f'{mode[0]}: Unknown mode prefix of file: {file}')

def sha256_hex(file):
    """Returns the hexadecimal text for SHA-256 hash value of the file."""
    a_hash = hashlib.sha256()
    with open(file, 'rb') as a_file:
        try:
            its_bytes = a_file.read()
        except OSError:
            return f'(unreadable)'
        a_hash.update(its_bytes)
    hexadecimal = a_hash.hexdigest()
    return hexadecimal

main(sys.argv)
