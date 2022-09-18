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

class FileInfo:
    """Class of File Information."""
    def __init__(self) -> None:
        """Initialize this instance."""

    def __repr__(self) -> str:
        """Returns instantiating representation."""
        return f'FileInfo()'

    @classmethod
    def fileinfo_help(cls, args):
        """Show help message."""
        FileInfo._put_message(f'fileinfo - List File attributes')
        FileInfo._put_message(f'[VERSION]')
        FileInfo._put_message(f'  {FileInfo._version()}')
        FileInfo._put_message(f'[COPYRIGHT]')
        FileInfo._put_message(f'  {FileInfo._copyright()}')
        FileInfo._put_message(f'[LICENSE]')
        FileInfo._put_message(f'  {FileInfo._license()}')
        FileInfo._put_message(f'[SYNOPSIS]')
        FileInfo._put_message(f'  {args[0]} [ File | Directory ]...')

    @staticmethod
    def _put_message(message):
        """Puts the message text into the standard out."""
        print(message)

    @classmethod
    def _version(cls):
        """Returns the version message."""
        return f'1.0.6 (2022/09/18) for Python 3.x or later; '\
            + f'(Tested for Python 3.6.8 on Redhat Enterprise Linux 8.2, '\
            + f'Python 3.7.4 on Windows 10 Pro 21H1 and for Python 3.9.1 on MacBook Pro; '\
            + f'Introduced the class FileInfo.)'

    @classmethod
    def _copyright(cls):
        """Returns the copyright notification."""
        return f'Copyright© 2022, kimura.shinichi@ieee.org'

    @classmethod
    def _license(cls):
        """Returns the license notification."""
        return f'Licensed by Apache License 2.0( {FileInfo._apache_license_url()} ) or later.'

    @classmethod
    def _apache_license_url(cls):
        """Returns the URL of The Apache Software Licence 2.0."""
        return f'https://www.apache.org/licenses/LICENSE-2.0'

    def run(self, args) -> int:
        """The main program entrance."""
        if len(args) < 2:
            self.fileinfo_help(args)
            return 1

        names = {'unames':{}, 'gnames':{}}
        for arg in args[1:]:
            self._dir_stat_invisibly(arg, names)
            self._show(arg, names)
        return 0

    def _dir_stat_invisibly(self, file, names):
        """
        Make the directory of the file or the current directory
        without showing fileinfo.
        """
        a_directory = os.path.dirname(file)
        if a_directory:
            self._stat_str(a_directory, names)
        else:
            self._stat_str('.', names)

    def _show(self, file, names):
        """Show the fileinfo of the file and / or its children."""
        FileInfo._put_fileinfo(self._stat_str(file, names))

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
                        self._show(child_path, names)
                    except PermissionError:
                        FileInfo._put_fileinfo(f'(Skipping {child_path})')
            except PermissionError:
                FileInfo._put_fileinfo(f'(Skipping children of {a_directory})')

    @staticmethod
    def _put_fileinfo(fileinfo_str):
        """Put a file-info string to the standard out."""
        print(fileinfo_str)

    @staticmethod
    def _stat_str(file, names):
        """
        Get a text representation of the stat values of the file
        using dictionary pair names.
        """
        if not os.path.exists(file):
            return f'{file}: No such file or directory.'

        stat_info = os.stat(file, follow_symlinks=False)
        path = pathlib.Path(file)
        mode = stat.filemode(stat_info.st_mode)
        dic = {
            'mode': mode,
            'nlink': stat_info.st_nlink,
            'uid': stat_info.st_uid,
            'path': path,
            'uname': FileInfo._get_uname(stat_info.st_uid, path, names['unames']),
            'gid': stat_info.st_gid,
            'gname': FileInfo._get_gname(stat_info.st_gid, path, names['gnames']),
            'size': stat_info.st_size,
            'hash': FileInfo._get_hash(file, mode),
            'mtime': FileInfo._as_datetime_style(stat_info.st_mtime),
            'link': FileInfo._get_link_symbol(path)
        }
        return '{0[mode]} {0[nlink]} ' \
            '{0[uname]}({0[uid]}):{0[gname]}({0[gid]}) ' \
            '{0[size]} {0[hash]} {0[mtime]} {0[path]}{0[link]}'.format(dic)

    @staticmethod
    def _get_uname(uid, path, unames):
        """Get the name of uid of the path with a dictionary unames."""
        return FileInfo._get_xname(uid, (lambda: FileInfo._get_owner(path)), unames)

    @staticmethod
    def _get_owner(path):
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

    @staticmethod
    def _get_gname(gid, path, gnames):
        """Get the name of gid group of the path with a dictionary gnames."""
        return FileInfo._get_xname(gid, (lambda: FileInfo._get_group(path)), gnames)

    @staticmethod
    def _get_group(path):
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

    @staticmethod
    def _get_xname(xid, fun, xnames):
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

    @staticmethod
    def _get_hash(file, mode):
        """Get a hash value of the file on its mode."""
        return f'SHA256:{FileInfo._sha256(file, mode)}'

    @staticmethod
    def _get_link_symbol(path):
        """Get a referring path of the symbolic link of that path."""
        if os.path.islink(path):
            try:
                link = f' -> {os.readlink(path)}'
            except FileNotFoundError:
                link = f' -> (No such file or directory)'
        else:
            link = ''
        return link

    @staticmethod
    def _as_datetime_style(timestamp):
        """Returns the text representation of the timestamp."""
        a_datetime = FileInfo._datetime_of(timestamp)
        return a_datetime.strftime('%Y/%m/%d %H:%M:%S')

    @staticmethod
    def _datetime_of(timestamp):
        """Returns the datetime of the timestamp."""
        return datetime.datetime.fromtimestamp(timestamp)

    @staticmethod
    def _sha256(file, mode):
        """
        Returns SHA-256 hash value hexadecimal text
        or some other text representation of the file
        which depends on its mode.
        """
        if mode[0] == '-':
            return FileInfo._sha256_hex(file)
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

    @staticmethod
    def _sha256_hex(file):
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

# main(sys.argv)
if __name__ == '__main__':
    A_FILEINFO = FileInfo()
    A_FILEINFO.run(sys.argv)
