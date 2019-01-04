#!/usr/bin/env python
# coding: utf-8

print('Hi, flashops')

import os, sys, json, traceback, argparse, webbrowser
from datetime import datetime, date, timedelta
from decimal import Decimal

import yaml

import six
from six.moves import input

from .syncutils import *

GV_FILENAME = ''
GV_CONFIG  = {}
GV_TEST = False
GV_batchvars = {}

K_OBJ_TYPES = ('servers', 'projects', 'tasks', )
K_TIPS1 = ['[f] Files', '[r] Projects', '[s] Servers', '[t] Tasks', '[c] Statements', '[D] Donation', '{}Please input your choice ("exit" for quit): ']
K_DIR_HOME = '/flashops'

K_ALL_COMMAND = ('/s', '/S', '/r', '/R', '/t', '/T', '/c', '/C', '/d', '/D', '/exit', '/quit', '/reload', '/env')
K_OBJ_COMMAND = [
    [('/r', '/R', 'r', 'R'), 'projects'],
    [('/s', '/S', 's', 'S'), 'servers'],
    [('/t', '/T', 't', 'T'), 'tasks'],
]

################################################################################

def flashops():
    # 入口
    global GV_CONFIG, GV_FILENAME, GV_TEST, K_TIPS1
    # 命令行
    parser = argparse.ArgumentParser()
    parser.add_argument("-f","--file", help="Indicate YAML config file, otherwise: $HOME/flashop.yaml")
    parser.add_argument("-v","--version", help="Show Version", action="store_true")
    parser.add_argument("-e","--env", help="Indicate environment variables (eg: WORKDIR=/mywork;)")
    parser.add_argument("-t","--test", help="Test environment", action="store_true")
    args = parser.parse_args()

    if args.version:
        six.print_('FlashOps Version: 19.01.02')
        return
    if args.file:
        GV_FILENAME = args.file
    else:
        six.print_('No config file provided, using FLASHOPS_FILE. -h to see the help.')
        if os.getenv('FLASHOPS_FILE'):
            GV_FILENAME = os.getenv('FLASHOPS_FILE')
        else:
            GV_FILENAME = os.path.join(os.getenv('HOME'), 'flashops.yml')
            if not os.path.isfile(GV_FILENAME):
                GV_FILENAME = os.path.join(os.getenv('HOME'), 'flashops.yaml')
    if not os.path.isfile(GV_FILENAME):
        six.print_('{} not exists!'.format(GV_FILENAME))
        return
    if args.env:
        for item in args.env.split(';'):
            key, val = item.split('=') if item.find('=')>0 else (item, '',)
            os.environ[key] = val
    GV_TEST = bool(args.test)
    load_config()
    main()

def load_config():
    global GV_CONFIG, GV_FILENAME
    GV_CONFIG = yaml.load(open(GV_FILENAME).read())
    for objtype in K_OBJ_TYPES:
        for x in GV_CONFIG.get(objtype, []):
            x['objtype'] = objtype
            if objtype in K_OBJ_TYPES[:2]:
                for y in x.get('operations', []):
                    if 'title' not in y:
                        y['title'] = 'Unknown'
            else:
                if 'title' not in x:
                    x['title'] = 'Unknown'
    # six.print_(json.dumps(GV_CONFIG, indent=4))

def parse_command(command):
    # 返回输入命令针对的对象类型 servers/projects/tasks，以及去掉命令后的子命令
    for x in K_OBJ_COMMAND:
        if command.startswith(x[0]):
            for y in x[0]: command = command.replace(y, '', 1)
            return x[1], command
    return None, None

def main():
    # 主函数。不用 cmd 模块主要是因为 cmd 模块是命令行形式的，需要输入命令。本程序要的效果是多级菜单式命令选择。
    global GV_CONFIG
    ltips = os.linesep.join(['File: '+os.path.realpath(GV_FILENAME)]+K_TIPS1).format(('TEST:' if GV_TEST else ''))
    command = input(ltips).strip()
    while command not in ('exit', 'quit', '/exit', '/quit'):
        if command in ('reload', '/reload'):
            load_config()
            command = input(ltips)
        elif command.startswith(('env', '/env')):
            filterkey = command.split(' ')
            filterkey = filterkey[-1].upper() if len(filterkey)>1 else None
            for k, v in os.environ.items():
                if not filterkey or (filterkey and (k.upper().find(filterkey)>=0 or v.upper().find(filterkey)>=0)):
                    six.print_('{}={}'.format(k, v))
            command = input(ltips)
        elif command.startswith( ('/f', '/F', 'f', 'F', ) ):
            select_file()
            ltips = os.linesep.join(['File: '+os.path.realpath(GV_FILENAME)]+K_TIPS1).format(('TEST:' if GV_TEST else ''))
            command = input(ltips)
        elif command.startswith( ('/c', '/C', 'c', 'C', ) ):
            filterkey = command.split(' ')
            filterkey = filterkey[-1].upper() if len(filterkey)>1 else None
            for row in GV_CONFIG.get('statements', []):
                if not filterkey or (filterkey and row.upper().find(filterkey)>=0):
                    six.print_(row)
            six.print_('')
            command = input(ltips)
        elif command.startswith( ('/d', '/D', 'd', 'D', ) ):
            webbrowser.open('https://github.com/dongyg/flashops#donation', new=2)
            six.print_('Please goto the web page just opened. Or access https://github.com/dongyg/flashops#donation by yourself.')
            command = input(ltips)
        elif command=='???': #测试用
            six.print_(GV_TEST)
            command = input(ltips)
        else:
            objtype, subcmd = parse_command(command)
            retval = select_item(objtype, initfunc=create_conn, subcmd=subcmd)
            command = retval if retval and retval.startswith(K_ALL_COMMAND) else input(ltips).strip()
    close_all_server()
    six.print_('See you')


################################################################################

class FlashJSONEncoder(json.JSONEncoder):
    """json模块不能直接编码日期时间类型，扩展JSONEncoder类处理日期时间类型，使用时dumps('',cls=FlashJSONEncoder)"""
    from fabric import Connection
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, Decimal):
            return "%.2f" % obj
        elif isinstance(obj, timedelta): # 对应mysql的time字段类型
            s = str(obj) # [H]H:MM:SS
            if len(s)==7:
                s = '0'+s
            return s
        elif isinstance(obj, Connection):
            return '<Object of Connection>'
        else:
            try:
                return json.JSONEncoder.default(self, obj)
            except:
                return obj.__name__ if hasattr(obj, '__name__') else ''

def ten_to_trsix(value):
    '''10进制转36进制'''
    # assert value >= 0
    stc = '0123456789abcdefghijklmnopqrstuvwxyz'
    base = len(stc)
    retval = ''
    intp, remp = divmod(value, base)
    while intp > 0:
        retval = stc[remp]+retval
        intp, remp = divmod(intp, base)
    retval = stc[remp]+retval
    return retval

def trsix_to_ten(value):
    '''36进制转10进制'''
    value = value.strip()
    stc = '0123456789abcdefghijklmnopqrstuvwxyz'
    base = len(stc)
    retval = 0
    weight = base ** (len(value)-1)
    for i,d in enumerate(value):
        retval += stc.find(d) * weight
        weight //= base
    return retval

def parse_vars1(content):
    # 解析变量，得到变量名列表
    import re
    pattern = re.compile('\{\{\w+\}\}')
    return set([x[2:-2] for x in pattern.findall(content)])

def parse_vars2(content):
    # 解析变量，得到变量名列表
    import re
    pattern = re.compile('##[|\%|\w]+##')
    return [x[2:-2] for x in pattern.findall(content)]

def fill_vars(content):
    # 解析变量并填充变量值后返回
    import pyperclip
    global GV_batchvars
    for key, val in GV_batchvars.items():
        content = content.replace(key, val)
    for var in parse_vars2(content):
        GV_batchvars['##'+var+'##'] = datetime.now().strftime(var)
    for var in parse_vars1(content):
        if var=='CLIPBOARD':
            val = pyperclip.paste()
        elif os.getenv(var):
            val = os.getenv(var)
        else:
            if var.lower().find('pass')>=0:
                import getpass
                val = getpass.getpass('Give the [' + var + ']: ')
            else:
                val = input('Give the [' + var + ']: ')
            if var.isupper():
                os.environ[var] = val
        GV_batchvars['{{'+var+'}}'] = val
    for key, val in GV_batchvars.items():
        content = content.replace(key, val)
    return content

def create_conn(obj):
    # 输入server/project，创建服务器连接，project直接使用invoke来执行本地shell命令
    if obj['objtype']==K_OBJ_TYPES[0]:
        if '_conn_' not in obj:
            if 'ssh' not in obj:
                six.print_('Server {} has no [ssh] config!'.format(obj['title']))
                return
            ssh_arg = {}
            if 'keyfile' in obj['ssh']:
                ssh_arg['key_filename'] = fill_vars(obj['ssh']['keyfile'])
            if 'keypass' in obj['ssh']:
                ssh_arg['password'] = fill_vars(obj['ssh']['keypass'])
            from fabric import Connection, Config
            if 'sudopass' in obj['ssh']:
                obj['_conn_'] = Connection(obj['ssh']['host'], user=obj['ssh']['user'], config=Config(overrides={'sudo': {'password': fill_vars(obj['ssh']['sudopass'])}}), connect_kwargs=ssh_arg)
            else:
                obj['_conn_'] = Connection(obj['ssh']['host'], user=obj['ssh']['user'], connect_kwargs=ssh_arg)
            six.print_('Connecting to {} ...... '.format(obj['title']), end='')
            sys.stdout.flush()
            six.print_('Work path: ', end='')
            obj['_conn_'].run('pwd')
    elif obj['objtype']==K_OBJ_TYPES[1]:
        if '_conn_' not in obj:
            import invoke
            obj['_conn_'] = invoke

def close_all_server():
    # 关闭所有server的连接
    global GV_CONFIG
    for i, server in enumerate(GV_CONFIG.get('servers', []), 1):
        if '_conn_' in server and hasattr(server['_conn_'], 'close'):
            server['_conn_'].close()
            six.print_('{} closed.'.format(server['title']))

def init_server_folder(conn):
    # 初始化远程机器上的flashops目录
    username = conn.run('whoami', hide=True).stdout.strip()
    for folder in [K_DIR_HOME, K_DIR_HOME+'/upcache', K_DIR_HOME+'/logs', K_DIR_HOME+'/tmp']:
        if conn.run('test -e {}'.format(folder), warn=True).failed:
            conn.sudo('mkdir {}'.format(folder))
            conn.sudo('chown {}:{} {}'.format(username, username, folder))
    return conn.run('test -e {}'.format(K_DIR_HOME), warn=True).ok

################################################################################
def select_file():
    # 选择当前目录下的 yaml/yml 文件
    global GV_CONFIG, GV_FILENAME
    fnames = [fname for fname in os.listdir('./') if fname.lower().endswith(('yaml','yml'))]
    if fnames:
        tips = ['[{}] {}'.format(ten_to_trsix(i), item) for i, item in enumerate(fnames, 1)]
        tips.append('Choose a config file: ')
        command = input(os.linesep.join(tips)).strip()
        idx = trsix_to_ten(command)-1
        if idx>=0 and idx<len(fnames):
            GV_FILENAME = fnames[idx]
            load_config()
    else:
        six.print_('No yaml files in current folder: {}.{}'.format(os.getcwd(), os.linesep))

def select_item(objtype, initfunc=None, subcmd=''):
    # 选择server/project/task
    if objtype not in ('servers', 'projects', 'tasks'): return
    if objtype not in GV_CONFIG:
        six.print_('No {} defined.'.format(objtype))
        return
    tips = ['[{}] {}'.format(ten_to_trsix(i), item['title']) for i, item in enumerate(GV_CONFIG.get(objtype, []), 1)]
    tips.append('{}Choose one of the {}: '.format(('TEST:' if GV_TEST else ''), objtype))
    command = subcmd or input(os.linesep.join(tips)).strip()
    while True:
        if command.startswith('/'): return command
        if command=='.': return command
        if command=='?':
            command = input(os.linesep.join(tips)).strip()
        elif command.startswith('?'):
            idx = trsix_to_ten(command[1:])-1
            if idx>=0 and idx<len(GV_CONFIG[objtype]):
                obj = GV_CONFIG[objtype][idx]
                six.print_(json.dumps(obj, cls=FlashJSONEncoder, indent=4))
            command = input(tips[-1]).strip()
        elif command!='':
            istest = command.startswith(('test:', 'TEST:')) #选择server/project/task时test:指令只对task有作用，传递给exec_task
            if istest: command = command.replace('test:','',1).replace('TEST:','',1)
            idx = trsix_to_ten(command)-1
            if idx>=0 and idx<len(GV_CONFIG[objtype]):
                obj = GV_CONFIG[objtype][idx]
                if initfunc and callable(initfunc): initfunc(obj)
                retval = select_operation(obj) if obj['objtype'] in K_OBJ_TYPES[:2] else exec_task(obj, istest)
                if retval and retval.startswith('/'):
                    return retval
                elif retval=='.':
                    six.print_(os.linesep.join(tips[:-1]).strip())
            command = input(tips[-1]).strip()
        else:
            command = input(tips[-1]).strip()

def get_operation(obj, command, _test_=None):
    # 根据输入快捷键或序号取得operation。先按序号查找，当快捷键与序号冲突的，先按序号查找能够保证所有操作都可达，冲突的快捷键会失效但仍可通过序号执行。反之若先查找快捷键冲突的序号将不可达
    operation = {}
    # 按序号匹配
    idx = trsix_to_ten(command)
    if idx==0:
        operation = {'type': '_checkconnection_'}
    elif idx>0 and idx<=len(obj['operations']):
        operation = obj['operations'][idx-1]
    # 按定义的快捷键匹配
    if not operation:
        for x in obj['operations']:
            if x.get('shortcut')==command:
                operation = x
    return operation

def select_operation(obj):
    # 选择server/project的operation并执行，输入obj为server或project的定义
    tips = ['[{}] {}{}'.format(ten_to_trsix(i), ('({})'.format(op['shortcut']) if op.get('shortcut') else ''), op['title']) for i, op in enumerate(obj.get('operations', []), 1) if op.get('visible',True)]
    tips.insert(0, '[0] Check connection')
    tips.append('{}({})Choose a Operation: '.format(('TEST:' if GV_TEST else ''), obj['title']))
    command = input(os.linesep.join(tips)).strip()
    while True:
        if command.startswith('/'): return command
        if command=='.': return command
        if command=='?':
            command = input(os.linesep.join(tips)).strip()
        elif command.startswith('?'):
            operation = get_operation(obj, command[1:].strip())
            six.print_(json.dumps(operation, indent=4))
            command = input(tips[-1]).strip()
        elif command!='':
            istest = command.startswith(('test:', 'TEST:'))
            if istest: command = command.replace('test:','',1).replace('TEST:','',1)
            operation = get_operation(obj, command)
            exec_operation(obj, operation, False, istest)
            command = input(tips[-1]).strip()
        else:
            command = input(tips[-1]).strip()

def exec_operation(objhost, operation, isbatch=False, _test_=None):
    # 实际执行operation。判断operation的type，处理includes，等等
    import pyperclip
    global GV_batchvars
    if not operation: return
    objtarget = get_obj_by_title(operation.get('target'), objhost)
    if '_conn_' not in objtarget:
        create_conn(objtarget)
    if operation.get('executor') and os.path.isfile(operation['executor']):
        scripts = open(operation['executor']).read()
        if scripts:
            exarg = {'operation':operation, 'objtarget':objtarget, 'objhost':objhost, 'get_obj_by_title':get_obj_by_title, 'get_obj_and_operation':get_obj_and_operation, 'create_conn':create_conn, 'init_server_folder':init_server_folder, 'fill_vars':fill_vars, 'K_DIR_HOME':K_DIR_HOME}
            try:
                c = compile(scripts,'','exec')
                six.exec_(c, exarg, exarg)
            except Exception as e:
                traceback.print_exc()
    elif operation.get('type')=='_checkconnection_':
        exec_checkconnection(objtarget)
    elif operation.get('type')=='gitpush' and 'folder' in operation:
        git_add_commit_push(objtarget, fill_vars(operation['folder']), _test_)
    elif operation.get('type')=='uploadfiles':
        exec_uploadfiles(operation, isbatch)
    elif operation.get('type')=='downfiles':
        exec_downloadfiles(objtarget, operation, isbatch)
    elif 'commands' in operation:
        if operation.get('yesorno'):
            yesorno = input('Run {}{}{}{}Continue?(y/n): '.format(operation['title'], os.linesep, os.linesep.join(operation['commands']), os.linesep, os.linesep)).strip()
            if yesorno in ('Y', 'y'):
                exec_commands(objtarget, operation['commands'], operation.get('issudo'), _test_)
        else:
            exec_commands(objtarget, operation['commands'], operation.get('issudo'), _test_)
    elif 'includes' in operation:
        exec_includes(objtarget, operation['includes'], isbatch, _test_)
    if not isbatch: GV_batchvars = {}

def exec_task(obj, _test_=None):
    # 执行task
    global GV_batchvars
    if 'operations' not in obj:
        six.print_('No operations!')
    else:
        for i, op in enumerate(obj['operations'],1):
            six.print_('Step{} - {}'.format(i, op['title']))
            exec_operation(obj, op, True, _test_)
        GV_batchvars = {}

def exec_commands(obj, commands, issudo=False, _test_=None):
    # 执行server或project的commands(仅commands定义的命令)
    if _test_==None: _test_ = GV_TEST
    for command in commands:
        command = fill_vars(command).strip()
        if command:
            six.print_(command)
            if not _test_:
                try:
                    if obj['_conn_']:
                        if hasattr(obj['_conn_'], 'is_connected') and not getattr(obj['_conn_'], 'is_connected'): #如果远程连接未建立先连接
                            obj['_conn_'].open()
                        if issudo:
                            obj['_conn_'].sudo(command, pty=True)
                        else:
                            obj['_conn_'].run(command, pty=True)
                except Exception as e:
                    traceback.print_exc()
                six.print_('')

def get_obj_by_title(typeandtitle, defaultobj=None):
    # 输入 servers.title 或 projects.title 得到 server/porject 对象。如果 title 能唯一确定对象，可以省略前面的 servers/projects
    retval = None
    if typeandtitle:
        typeandtitle = typeandtitle.split('.')
        dst = []
        tlt = ''
        if len(typeandtitle)==2:
            dst.append(typeandtitle[0])
            tlt = typeandtitle[1]
        elif len(typeandtitle)==1:
            dst.append('servers')
            dst.append('projects')
            tlt = typeandtitle[0]
        for objtype in dst:
            for x in GV_CONFIG.get(objtype, []):
                if x['objtype']==objtype and x['title']==tlt:
                    retval = x
    return retval or defaultobj

def get_obj_and_op_by_title(namespace, obj):
    # 根据对象(server/project/task)的title，得到对象。根据操作的title得到operation/task
    # 返回两个变量 (对象，操作) tuple 构成的数组。因为可能给定的namespace是不正在的，返回值用数组的形式可以明确知道是否找到了匹配的
    global GV_CONFIG
    path = namespace.split('.')
    objtype, objtitle, optitle = None, None, None
    if len(path)==3:    # servers.vs28.restartwww, projects.www.synccode, tasks.?.?
        objtype, objtitle, optitle = path
    elif len(path)==2:  # vs28.restartwww, www.synccode, tasks.commit_and_restart
        if path[0]=='tasks':
            objtype, objtitle = path
        else:
            objtype, objtitle, optitle = obj['objtype'], path
    elif len(path)==1:  # restartwww, synccode, commit_and_restart
        objtype, objtitle, optitle = obj['objtype'], obj['title'], path[0]
    retval = []
    for x in GV_CONFIG.get(objtype, []):
        if x['objtype']==objtype and x['title']==objtitle:
            for y in x.get('operations', []):
                if y['title']==optitle or (x['objtype']=='tasks' and not optitle):
                    retval.append( (x, y) )
    return retval
def get_obj_and_operation(namespace):
    retval = get_obj_and_op_by_title(namespace, None)
    if retval:
        return retval[0]
    else:
        return None, None

def parse_includes(includes, obj):
    # 解析includes指令包含的operation, 输入obj是includes指令所属的server/project/task，当includes指令给出的引用操作未指定归属时，只在其所属对象中查找
    # 返回includes指令包含的operation，及其对应的对象 ((operation, server/project/task),)
    retval = []
    for namespace in includes:
        retval.extend( get_obj_and_op_by_title(namespace, obj) )
    return retval

def exec_includes(obj, includes, isbatch=False, _test_=None):
    # 执行 server/project/task 的includes定义所包含的所有operations，支持includes嵌套
    global GV_batchvars
    ops = parse_includes(includes, obj)
    for obj, op in ops:
        # print '-'*10, obj['objtype'], obj['title'], op['title']
        if obj and op:
            exec_operation(obj, op, True, _test_)
        if not isbatch: GV_batchvars = {}


################################################################################

def exec_checkconnection(obj):
    # 检查测试连接
    if hasattr(obj['_conn_'], 'is_connected'):
        try:
            ret = obj['_conn_'].run('pwd', pty=False, hide=True)
            resp = ret.stdout.strip()
        except Exception as e:
            try:
                ret = obj['_conn_'].run('pwd', pty=False, hide=True) # 第1次失败后再执行一次会自动建立连接
                resp = ret.stdout.strip()
            except Exception as e:
                resp = 'Unknown' # 若两次都失败，连接就是断开的，打印工作目录 Unknown
        six.print_('Checking {}: {}. Work dir: {}'.format(obj['title'], getattr(obj['_conn_'], 'is_connected'), resp))
    else:
        ret = obj['_conn_'].run('pwd', pty=False, hide=True)
        resp = ret.stdout.strip()
        six.print_('Checking {}: Local. Work dir: {}'.format(obj['title'], resp))

def exec_uploadfiles(operation, isbatch=False):
    # 复制文件至远端。
    # 源是目录时，末尾是斜杠只压缩目录里面内容，末尾非斜杠压缩目录本身，目地必须是目录（若不存在则创建一个目录），非全量时根据目地目录中已经存在的文件修改时间和大小壮士判断需要同步的源文件
    # 源是文件时，比较简单，复制即可
    six.print_('Preparing ({}) ...'.format('total syncs' if operation.get('fullordiff', 'diff')=='full' else 'delta syncs'))
    for source, target in operation.get('sources',{}).items():
        srcname = fill_vars(source)
        if not os.path.isdir(srcname) and not os.path.isfile(srcname):
            six.print_('[{}] not exists!'.format(srcname))
            continue
        isdir, basename, transsrc, transdst = getnames(srcname)
        if not isdir: # 打包文件
            pack_file(srcname, transsrc)
        else:         # 打包目录
            # 只有全目录压缩才需要在此时打包，差异同步需要针对每个服务器的目的目录进行比较后打包
            if operation.get('fullordiff', 'diff')=='full':
                pack_folder(srcname, transsrc, 'full', conn=None, dstname='', issudo=operation.get('issudo', False), verbose=False, excludes=operation.get('excludes',[]))
        for srvname, dstname in target.items():
            # 初始化服务器连接、目录等
            server = get_obj_by_title(srvname)
            dstname = fill_vars(dstname)
            create_conn(server)
            if '_conn_' not in server: continue
            if not init_server_folder(server['_conn_']): continue
            # 如果同步源是目录并且差异同步，需要从服务器上的目录获取文件信息，与源进行比较，得到有差异的文件，只打包这些文件，源中转文件名、目的中转文件名要有所不同，包含目标服务器名
            if isdir and operation.get('fullordiff', 'diff')=='diff':
                transsrc = transsrc.replace('.tar.gz', '_{}.tar.gz'.format(srvname))
                transdst = transdst.replace('.tar.gz', '_{}.tar.gz'.format(srvname))
                pack_folder(srcname, transsrc, 'diff', conn=server['_conn_'], dstname=dstname, issudo=operation.get('issudo', False), verbose=True, excludes=operation.get('excludes',[]))
            # 复制到中转目录
            if not os.path.isfile(transsrc): # 如果中转文件不存在就跳过
                continue
            six.print_('Uploading... {} > {}'.format(transsrc, transdst))
            server['_conn_'].put(transsrc, transdst)
            # 在服务器上解压文件
            six.print_('Extracting... {} > {}'.format(transdst, dstname))
            cmdprefix = 'sudo ' if operation.get('issudo', False) else ''
            if server['_conn_'].run('test -e {}'.format(dstname), warn=True).failed:
                server['_conn_'].run('mkdir {}'.format(dstname))
            server['_conn_'].run('{}tar -C {} -xzf {}'.format(cmdprefix, dstname, transdst), pty=True)
            # 源中转文件是针对服务器的时候，循环内删除
            if isdir and operation.get('fullordiff', 'diff')=='diff':
                if os.path.isfile(transsrc):
                    six.print_('Removing... {}'.format(transsrc))
                    os.remove(transsrc)
        if os.path.isfile(transsrc):
            six.print_('Removing... {}'.format(transsrc))
            os.remove(transsrc)
    six.print_('Done.')

def exec_downloadfiles(obj, operation, isbatch=False):
    # 下载文件
    global GV_batchvars
    yyyymmddhhnnss = "%Y%m%d%H%M%S"
    if operation.get('files',{}).keys():
        six.print_('Downloading...')
    for source, target in operation.get('files',{}).items():
        source = fill_vars(source)
        if source[-1]=='/': source = source[:-1] #源如果是/结尾去掉它
        target = fill_vars(target)
        # 如果源目录或文件不存在，跳过
        if obj['_conn_'].run('test -e {}'.format(source), warn=True).failed:
            six.print_('Source file or folder not exists: {}'.format(source))
            continue
        # 如果目标不存在且目标的父目录不存在，跳过
        if not os.path.exists(target) and not os.path.exists(os.path.split(target)[0]):
            six.print_('Destination or parent folder not exists: {}'.format(target))
            continue
        # 如果源是目录，目标不能是文件
        isfolder = obj['_conn_'].run('test -d {}'.format(source), warn=True).ok
        isfile = obj['_conn_'].run('test -f {}'.format(source), warn=True).ok
        if isfolder and os.path.isfile(target):
            six.print_('Source is a folder, can not download to a file: {}'.format(target))
            continue
        tarfilename = '{}_{}.tar.gz'.format(os.path.basename(source), datetime.strftime(datetime.now(), yyyymmddhhnnss))
        # 如果目标是目录，使目标文件名与源文件名相同
        target = os.path.join(target, os.path.basename(source)) if os.path.isdir(target) else target
        # 开始下载
        six.print_('{} > {}'.format(source, target))
        try:
            if isfolder or operation.get('compress', False): #下载前压缩
                # 用 tar 命令压缩像日志文件这种动态在变化的文件时，检查到文件会压缩失败，如果不捕获异常的话，异常会跳出 flashops
                srcpath = os.path.split(source)[0]
                srcfilename = '/flashops/tmp/{}'.format(tarfilename)
                dstfilename = os.path.join(os.path.split(target)[0], tarfilename)
                obj['_conn_'].run('cd {} && tar -czf {} {}'.format(srcpath, srcfilename, os.path.basename(source)), pty=True)
                obj['_conn_'].get(srcfilename, dstfilename)
            else:
                obj['_conn_'].get(source, target)
            if isfolder or operation.get('compress', False): #下载后解压
                dstfilename = os.path.join(os.path.split(target)[0], tarfilename)
                import tarfile
                tarobj = tarfile.open(dstfilename, 'r:gz')
                tarobj.extractall(os.path.split(target)[0]) #解压到目标目录
                tarobj.close()
                if isfile and os.path.basename(source)!=os.path.basename(target): #如果源是文件，解压出来的文件可能需要改名
                    os.rename(os.path.join(os.path.split(target)[0], os.path.basename(source)), target)
                os.remove(dstfilename) #删除压缩文件
        except Exception as e:
            traceback.print_exc()
    if not isbatch: GV_batchvars = {}

def git_add_commit_push(obj, gitpath, _test_=None):
    # git本地复本完整提交过程
    # gitpath = '/Users/vs/Projects/vansky'
    if _test_==None: _test_ = GV_TEST
    command = 'git -C {} status -s'.format(gitpath)
    six.print_(command)
    if _test_: return
    ret = obj['_conn_'].run(command, pty=True, hide=True)
    from cStringIO import StringIO
    fakefile = StringIO()
    fakefile.write(ret.stdout)
    filenames = []
    fakefile.seek(0)
    row = fakefile.readline()
    while row:
        filenames.append(row.split(' ')[-1])
        six.print_('[{}] {}'.format(len(filenames), row.strip()))
        row = fakefile.readline()
    fakefile.close()
    if not filenames:
        six.print_('Nothing to commit, working directory clean')
        return
    commits = []
    nos = input("Enter the numbers you want to submit(A for All): ").strip()
    if not nos:
        six.print_("You didn't select any files.")
        return
    if nos in ('A'):
        commits = filenames
    else:
        for no in nos.split(' '):
            if no.isdigit() and int(no)>0 and int(no)<=len(filenames):
                commits.append(filenames[int(no)-1])
    if commits:
        command = 'git -C {} add {}'.format(gitpath, ' '.join([os.path.join(gitpath, x.strip()) for x in commits]))
        six.print_(command)
        obj['_conn_'].run(command, pty=True)
        summary = input("Enter summit message: ").strip()
        if summary:
            command = 'git -C {} commit -m "{}"'.format(gitpath, summary)
            six.print_(command)
            obj['_conn_'].run(command, pty=True)
            command = 'git -C {} push'.format(gitpath)
            six.print_(command)
            obj['_conn_'].run(command, pty=True)
        else:
            six.print_("You didn't give commit message.")
    else:
        six.print_("You didn't select any files.")

if __name__ == '__main__':
    flashops()
