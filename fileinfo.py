import dataclasses
import datetime
import glob
import hashlib
import os
import pathlib
import stat
import sys

@dataclasses.dataclass
class Names:
  unames: dict
  gnames: dict

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
  return f'1.0.0 for Python 3.x or later; (Tested for Python 3.9.1 on MacBook Pro)'

def copyright():
  return f'Copyright© 2022/08/28, kimura.shinichi@ieee.org'

def license():
  return f'Licensed by Apache License 2.0( {apache_license_url()} ) or later.'

def apache_license_url():
  return f'https://www.apache.org/licenses/LICENSE-2.0'

def main(args) -> int:
  if len(args) < 2:
    help(args)
    return 1

  names = Names(unames={}, gnames={})
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
  uname = get_uname(uid, path, names.unames)
  gid = s.st_gid
  gname = get_gname(gid, path, names.gnames)
  size = s.st_size
  hash = get_hash(file, mode)
  mtime = as_Ymd_HMS(s.st_mtime)
  link = get_link_symbol(path)
  return f'{mode} {nlink} {uname}({uid}):{gname}({gid}) {size} {hash} {mtime} {path}{link}'

def get_uname(uid, path, unames):
  return get_xname(uid, path.owner, unames)

def get_gname(gid, path, gnames):
  return get_xname(gid, path.group, gnames)

def get_xname(xid, fun, xnames):
  if xid in xnames:
    xname = xnames[xid]
  else:
    try:
      xname = fun()
    except KeyError:
      xname = '(missing)'
    xnames[xid] = xname
  return xname

def get_hash(file, mode):
  return f'SHA256:{sha256(file, mode)}'

def get_link_symbol(path):
  if os.path.islink(path):
    link = f' -> {os.readlink(path)}'
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
  elif 'b' == mode[0]:
    return f'block-special'
  elif 'c' == mode[0]:
    return f'character-special'
  elif 'l' == mode[0]:
    return f'symbolic-link'
  elif 's' == mode[0]:
    return f'socket'
  elif 'P' == mode[0]:
    return f'FIFO'
  else:
    raise TypeError(f'{mode[0]}: Unknown mode prefix of file: {file}')

def sha256_hex(file):
  m = hashlib.sha256()
  with open(file, 'rb') as f:
    bytes = f.read()
    m.update(bytes)
  hex = m.hexdigest()
  return hex

main(sys.argv)
