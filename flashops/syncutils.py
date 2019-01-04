#!/usr/bin/env python
# coding: utf-8

__all__ = [
    'pack_file', 'pack_folder', 'getnames'
]

import os, fnmatch, json, traceback
from datetime import datetime
import six
from six.moves import input

K_DIR_HOME = '/flashops'

def list_destfiles(conn, destdir, issudo=False):
    # 得到目标目录中的文件清单，文件名:(d/-,大小,修改时间)。如果目标目录不存在则创建，issudo指示是否用root身份创建
    # 使用 find 命令列出来的文件名有个注意事项，将目标目录末尾无斜杠时，列出文件名以斜杠开头。将目标目录末尾有斜杠时，列出文件名则无斜杠开头
    cmdprefix = 'sudo ' if issudo else ''
    filedict = {}
    if conn.run('{}test -e {}'.format(cmdprefix, destdir), warn=True).failed:
        conn.run('{}mkdir -p {}'.format(cmdprefix, destdir))
    else:
        resp = conn.run('{}find {} | xargs ls -ld --time-style="+%Y-%m-%d %H:%M:%S"'.format(cmdprefix, destdir), hide=True)
        from cStringIO import StringIO
        fakefile = StringIO()
        fakefile.write(resp.stdout.strip())
        filenames = []
        fakefile.seek(0)
        row = fakefile.readline()
        while row:
            row = row.split(' ')
            filedict[row[-1].strip().replace(destdir,'',1)] = (row[0][0], row[-4], row[-3]+' '+row[-2])
            row = fakefile.readline()
        fakefile.close()
    return filedict

def toSeconds(timeDateStr):
    import time, datetime
    time1 = datetime.datetime.strptime(timeDateStr,"%Y-%m-%d %H:%M:%S")
    return time.mktime(time1.timetuple())
def toTime(manyseconds):
    import time,datetime
    timeArray = time.localtime(manyseconds) #1970秒数
    return time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    # return datetime.datetime.strptime(otherStyleTime, "%Y-%m-%d %H:%M:%S")

def excludeFile(filename, excludes=[]):
    #排除文件
    for x in excludes:
        if fnmatch.fnmatch(filename, x):
            return True

def filter_diff(srcinfo, dstinfo):
    # 比较源文件和目标文件的属性。srcinfo为os.stat返回值，dstinfo:(d/-,大小,修改时间)。不同或目标文件属性为空返回True，表示文件不同
    # print srcinfo.st_size, srcinfo.st_mtime, toSeconds(dstinfo[2]), dstinfo
    if dstinfo:
        if dstinfo[0]!='d':
            if int(dstinfo[1])!=srcinfo.st_size or toSeconds(dstinfo[2])<srcinfo.st_mtime:
                return True
    else:
        return True

def filter_files(srcname, dstfiles={}, onlydiff=True, excludes=[]):
    # 遍历源目录/文件，与目标目录/文件进行比较，onlydiff为True时得到源中更新的或不同的文件清单，否则为源中所有文件清单。onlydiff为False时dstfiles可以为空字典
    # dstfiles, 文件名:(d/-,大小,修改时间)
    retval = []
    if os.path.isfile(srcname):
        srcinfo = os.stat(srcname)
        dstinfo = dstfiles.get('')
        if filter_diff(srcinfo, dstinfo):
            retval.append(srcname)
        else:
            dstinfo = dstfiles.get(os.path.basename(srcname))
            if filter_diff(srcinfo, dstinfo):
                retval.append(srcname)
    elif os.path.isdir(srcname):
        for root, dirs, files in os.walk(srcname):
            relative_path = root.replace(srcname, "")
            if os.path.basename(srcname)!='': #目录名称末尾无斜杠时，relative_path会以斜杠开头，把它去掉
                relative_path = relative_path[1:]
            # 非onlydiff时，或onlydiff时目标中无当前目录时，当前目前需要包含在内。注：目录不需要添加到压缩包，只添加目录中的文件即可
            if not onlydiff or (onlydiff and not dstfiles.has_key(relative_path)):
                retval.append(relative_path)
            for fn0 in files:
                if excludeFile(fn0, excludes): continue #排除无用的系统产生的文件
                fnr = os.path.join(relative_path, fn0)
                fnw = os.path.join(root, fn0)
                statinfo = os.stat(fnw)
                # print fnr,
                # 非onlydiff时，或onlydiff时目标中无当前文件时，或目标中文件与当前文件大小或时间不同时
                if not onlydiff or (onlydiff and filter_diff(statinfo, dstfiles.get(fnr))):
                    retval.append(fnr)
    return retval

def pack_folder(srcname, pkgfile, fullordiff, conn, dstname, issudo=False, verbose=False, excludes=[]):
    # 打包压缩指定目录
    # srcname - 源目录
    # pkgfile - 打包压缩后存储文件名
    # fullordiff - full/diff 表示全目录压缩还是差异压缩
    # conn - 差异压缩时，需要取服务器端文件信息以便做对比，conn是Fabric的Connection对象，可以连接到服务器
    # dstname - 差异压缩时，服务器的目标目录名
    # issudo - 在服务器上执行命令时是否用sudo形式
    # verbose - 打印压缩的文件或目录名称。全量压缩时，只会包含第一级文件或目录名称
    # excludes - 要排除的文件
    import tarfile, os
    curdir = os.getcwd()
    os.chdir(os.path.join(srcname, '..')) #当前目录改为源目录的父目录
    pardir = os.getcwd()
    basename = srcname.replace(pardir, '').replace(os.sep, '')
    packfiles = []
    excludes.extend(['.DS_Store', 'Thumbs.db'])
    try:
        # 如果压缩整个目录，只要添加目录本身，或目录下第一层子目录或文件即可
        if fullordiff=='full':
            if os.path.basename(srcname)=='': #末尾斜杠表示压缩目录里面的内容不压缩目录本身
                os.chdir(srcname) #压缩目录里面内容时，必须要使源目录为当前目录
                for n in os.listdir(srcname):
                    if not excludeFile(n, excludes):
                        packfiles.append(n)
            else: #末尾没有斜杠表示压缩这个目录，压缩目录本身时，保持父目录为当前目录
                packfiles.append(basename)
        # 如果只压缩不同的文件，需要遍历目的目录得到每个文件的大小的修改时间，再遍历源目录，一个个文件进行对比
        else:
            dstfiles = list_destfiles(conn, dstname, issudo)
            # print json.dumps(dstfiles, indent=4)
            ftfiles = filter_files(srcname, dstfiles=dstfiles, onlydiff=True, excludes=excludes)
            # print json.dumps(ftfiles, indent=4)
            os.chdir(srcname) #差异同步时，过滤得到的差异文件名是相对路径，必须要使源目录为当前目录
            for n in ftfiles:
                if n and (os.path.isfile(n) or os.path.isdir(n)):
                    packfiles.append(n)
        if packfiles:
            six.print_('Packing... {} > {}'.format(srcname, pkgfile))
            six.print_('Count: {}'.format(len(packfiles)))
            tar = tarfile.open(pkgfile, 'w:gz')
            for n in packfiles:
                if verbose: six.print_(n)
                tar.add(n)
            tar.close()
        else:
            six.print_('No files need to sync.')
    except Exception as e:
        traceback.print_exc()
    finally:
        os.chdir(curdir)
    return os.path.isfile(pkgfile)

def pack_file(srcname, pkgfile):
    # 打包压缩指定文件
    import tarfile, os
    curdir = os.getcwd()
    os.chdir(os.path.split(srcname)[0])
    try:
        six.print_('Packing... {} > {}'.format(srcname, pkgfile))
        tar = tarfile.open(pkgfile, 'w:gz')
        tar.add(os.path.basename(srcname))
        tar.close()
    except Exception as e:
        traceback.print_exc()
    finally:
        os.chdir(curdir)
    return os.path.isfile(pkgfile)

def getnames(srcname):
    # 返回源文件或目录：是否目录、名称、本地临时文件名、服务器中转文件名
    global K_DIR_HOME
    yyyymmddhhnnss = "%Y%m%d%H%M%S"
    isdir = os.path.isdir(srcname)
    # 源中转压缩文件名，放在源目录下，同步后删掉
    if isdir and srcname[-1]=='/':
        basename = os.path.basename(srcname[:-1])
        transsrc = '{}_{}.tar.gz'.format(srcname+basename, datetime.strftime(datetime.now(), yyyymmddhhnnss))
    else:
        basename = os.path.basename(srcname)
        transsrc = '{}_{}.tar.gz'.format(srcname, datetime.strftime(datetime.now(), yyyymmddhhnnss))
    # 目标中转文件名，放在服务器的 upcache 下，同步后不删除
    transdst = '{}/upcache/{}_{}.tar.gz'.format(K_DIR_HOME, basename, datetime.strftime(datetime.now(), yyyymmddhhnnss))
    return isdir, basename, transsrc, transdst
