"""
Generates file information text list such as the output of UNIX/Linux ls -l.
"""
import argparse
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
    def __init__(self, argv) -> None:
        """Initialize this instance."""
        self.parser, self.args = FileInfo._parse_args(argv)
        self.my_out = sys.stdout

    def __repr__(self) -> str:
        """Returns instantiating representation."""
        return 'FileInfo()'

    @classmethod
    def _parse_args(cls, argv):
        """Parses argv and retuens parser and parsed args."""
        parser = argparse.ArgumentParser(
                prog='fileinfo.py',
                description='List File attributes'
            )
        parser.add_argument('FileEntry', nargs='*',
            help='File or Directory, '
            'both absolute path and relative path are acceptable.')
        parser.add_argument('-v', '--version', action='store_true',
            help='show version and exit')
        parser.add_argument('-c', '--copyright', action='store_true',
            help='show copyright and exit')
        parser.add_argument('-L', '--licence', action='store_true',
            help='show licence and exit')
        parser.add_argument('-r', '--recursive', action='store_true',
            help='process recursively into sub directories')
        parser.add_argument('-x', '--excludes',
            help='process skipping the specified sub directories and its children')
        parser.add_argument('-o', '--output',
            help='output file information list into the specified file')
        parser.add_argument('-f', '--force', action='store_true',
            help='force to output even if the output file is exists')
        args = vars(parser.parse_args(argv[1:]))
        return parser, args

    @classmethod
    def _print_help(cls, parser: argparse.ArgumentParser):
        """Show help message."""
        FileInfo._put_message(parser.format_help())
        FileInfo._print_version()
        FileInfo._put_message('')
        FileInfo._print_copyright()
        FileInfo._put_message('')
        FileInfo._print_licence()

    @staticmethod
    def _put_message(message):
        """Puts the message text into the standard out."""
        print(message)

    @classmethod
    def _print_version(cls):
        FileInfo._put_message('version:')
        FileInfo._put_message(f'  {FileInfo._version()}')

    @classmethod
    def _print_copyright(cls):
        FileInfo._put_message('copyright:')
        FileInfo._put_message(f'  {FileInfo._copyright()}')

    @classmethod
    def _print_licence(cls):
        FileInfo._put_message('licence:')
        FileInfo._put_message(f'  {FileInfo._licence()}')

    @classmethod
    def _version(cls):
        """Returns the version message."""
        return '1.0.10 (2022/09/19) for Python 3.x or later; '\
            + '(Tested for Python 3.6.8 on Redhat Enterprise Linux 8.2, '\
            + 'Python 3.7.4 on Windows 10 Pro 21H1 and for Python 3.9.1 on MacBook Pro; '\
            + 'Added optional args -o, --output and -f, --force.)'

    @classmethod
    def _copyright(cls):
        """Returns the copyright notification."""
        return 'Copyright© 2022, kimura.shinichi@ieee.org'

    @classmethod
    def _licence(cls):
        """Returns the licence notification."""
        return f'Licenced by Apache License 2.0( {FileInfo._apache_licence_url()} ) or later.'

    @classmethod
    def _apache_licence_url(cls):
        """Returns the URL of The Apache Software Licence 2.0."""
        return 'https://www.apache.org/licenses/LICENSE-2.0'

    def _warn(self, *message):
        concatenated = ' '.join(message)
        print(f'WARNING: {concatenated}', file=sys.stderr)

    def _error(self, *message):
        concatenated = ' '.join(message)
        print(f'ERROR: {concatenated}', file=sys.stderr)

    def _check_optional_args(self, args):
        """Returns go(True) or no-go(False) judged by optional args."""
        if args['version']:
            FileInfo._print_version()
            return False

        if args['copyright']:
            FileInfo._print_copyright()
            return False

        if args['licence']:
            FileInfo._print_licence()
            return False

        return True

    def run(self) -> int:
        """
        The main program entrance.

        Returns 0 if it ends normally.
        Returns 1 if it ends by help.
        Returns 2 if it ends abnormally.
        """
        parser, args = self.parser, self.args
        go_ahead = self._check_optional_args(args)
        if not go_ahead:
            return 1

        files = args['FileEntry']
        if len(files) < 1:
            self._print_help(parser)
            return 1

        output_file = args['output']
        ret = 0
        if output_file is None:
            ret = self._try_to_show(files, output_file=None)
        elif os.path.exists(output_file):
            if os.access(output_file, os.W_OK):
                if args['force']:
                    ret = self._try_to_show(files, output_file=output_file)
                else:
                    self._error(
                        f'Already exists the output file: {output_file}: '
                        '(Use -f option to overwrite)')
                    ret = 2
            else:
                self._error(f'The output file is not a writable: {output_file}')
                ret = 2
        else:
            ret = self._try_to_show(files, output_file=output_file)
        return ret

    def _show_all(self, files, out):
        self.my_out = out
        names = {'unames':{}, 'gnames':{}}
        for file in files:
            self._dir_stat_invisibly(file, names)
            self._show(file, names)

    def _try_to_show(self, files, output_file):
        if output_file is None:
            self._show_all(files, sys.stdout)
            return 0

        try:
            with open(file=output_file, mode='w', encoding='UTF-8') as my_out:
                self._show_all(files, my_out)
            return 0
        except IOError as io_error:
            self._error(f'Failed to write: {output_file}: {io_error}')
            return 2
        finally:
            self.my_out = sys.stdout

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
        self._put_fileinfo(self._stat_str(file, names))

        if not self.args['recursive']:
            return

        file_path = pathlib.Path(file)
        if os.path.isdir(file_path):
            # Do not follow any symbolic links.
            if os.path.islink(file_path):
                return
            a_directory = file_path
            try:
                # Show about all the children of a_directory.
                children = a_directory.glob('*')
                exs = self.args['excludes']
                excludes_list = str(exs).split(';')
                for child in children:
                    if child.name in excludes_list:
                        self._warn(f'Skiping sub-directory {child}')
                        continue
                    try:
                        child_path = f'{child}'
                        self._show(child_path, names)
                    except PermissionError:
                        self._put_fileinfo(f'(Skipping {child_path})')
            except PermissionError:
                self._put_fileinfo(f'(Skipping children of {a_directory})')

    def _put_fileinfo(self, fileinfo_str):
        """Put a file-info string to the standard out."""
        print(fileinfo_str, file=self.my_out)

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
        return ('{0[mode]} {0[nlink]} ' \
            + '{0[uname]}({0[uid]}):{0[gname]}({0[gid]}) ' \
            + '{0[size]} {0[hash]} {0[mtime]} {0[path]}{0[link]}').format(dic)

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
                link = ' -> (No such file or directory)'
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
        if mode[0] in a_dict:
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
                return '(unreadable)'
            a_hash.update(its_bytes)
        hexadecimal = a_hash.hexdigest()
        return hexadecimal

if __name__ == '__main__':
    FileInfo(sys.argv).run()
