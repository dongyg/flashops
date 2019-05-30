
## FlashOps 是什么

FlashOps 一词来源于 Flash 和 Operation 这两个词的组合。它是一个工具，可以简化通过 SSH 管理 Linux 服务器的操作过程。你经常要执行的一条命令或一组操作，可以简化为只输入一两个字符便可完成。

你可能会想到，一组操作，那么写脚本文件不就行了。FlashOps能做的不止如此，你可以认为它是用来组合脚本的，包含本地和远程操作，都可以组合起来一键完成。它还提供了上传、下载文件或目录的功能，在本地与远端之间传输同步文件更方便。


## 如何获得 FlashOps

FlashOps 使用 python 编写，同时支持 python2 和 python3，依赖 [Fabric](https://pypi.org/project/Fabric/), [YAML](https://pypi.org/project/PyYAML/) 库。可以简单地使用 pip 来安装。

```
pip install flashops
```


## 如何使用 FlashOps

### 前提

FlashOps 利用 Fabric 通过 ssh 管理远端 Linux 服务器，使用 FlashOps 之前，请确认你可以正常通过 ssh 连接和管理你的 Linux 服务器。

### 概念

FlashOps 定义了4类工作，分别是：

- 项目（projects）
- 服务器（servers）
- 任务（tasks）
- 语句（statements）

#### 操作

FlashOps 中定义`操作(Operation)`为工作的最小单位，它可以定义在 项目、服务器、任务 中。一个操作可以是一系列shell语句，或可以在shell下执行或调用的程序。可以是其它若干个操作的组合。此外 FlashOps 还提供了一些预置类型的操作。

### 配置

FlashOps 使用 yaml 格式文件作为配置文件，所有的东西都写在配置文件中。

```yaml
- projects。针对用户本机某个软件系统项目的管理，定义若干个操作。
    - title, 项目全称
    - operations, 定义该项目可以进行的操作
- servers。针对远端Linux服务器，定义每个服务器的连接及在其上可执行的若干个操作。
    - title, 服务器全称
    - ssh, 定义通过 ssh 连接服务器的连接参数
        - host, 远端 Linux 服务器地址
        - port, 远端 Linux 服务器 SSH 服务的端口，默认为 22
        - user, 连接到远端 Linux 服务器的用户名。不提供时将像使用 ssh 命令一样使用默认用户名
        - sudopass, 在 Linux 服务器上用 sudo 方式执行命令时提供的密码。另外也可以在命令中给出（明文给出显然不安全），可以在命令中使用变量，关于变量的使用见后面章节说明。也可在命令执行时交互式提供密码。
        - keyfile, 通过 SSH 连接时使用的证书。不提供时将像使用 ssh 命令一样使用 .ssh 目录下默认证书
        - keypass, 使用指定证书时，若证书文件需要密码，可以给出密码。同样明文给出是不安全的，可以使用变量。
    - operations, 同上
- tasks。将项目或服务器中定义的多个操作组合成一个完整的任务。
    - title, 任务全称
    - operations, 同上
- statements。经常使用的命令或语句之类的字符串，定义在这里。在 FlashOps 中可以迅速列出，并过滤，方便查阅，可复制使用。
```

#### 操作配置项

```yaml
title: 操作全称，可以被 includes 指令引用，可以有空格，不要重名，重名的 title 不光在引用时，在使用时也无法分辨它们
type: 操作类型，详见【预置操作类型】。未设置表示普通操作，由 commands 给出要执行的命令
commands: 对普通操作，可设置多条 shell 命令或可在 shell 下执行的文件
issudo: 针对 server 有效，指示是否使用 sudo 方式执行命令
yesorno: 执行前是否询问继续，默认为False
target: 针对 task 有效，当 operations 中定义具体的操作时，而不是 includes servers 或 projects 中的操作时，需要给出操作在哪里执行，哪个 project 或 server。使用 [servers.|projects.]title 形式给出
visible: 定义操作是否可见，默认为可见。注意即使操作不可见，其序号位还是占用的，可见的操作序号会不连续。输入此不可见操作的序号仍然可以执行它。不可见的意义在于它几乎是不会直接执行的，主要是用于被其它操作引用
shortcut: 定义命令快捷键，序号优先于快捷键，所以定义快捷键不要与序号冲突，否则快捷键无效。可以使用两个大写字母（序号只会是小写字母），即不会冲突，也容易记忆和输入
includes: 包含多个其它操作，使用 `[servers.][server title.]operation title` 的形式代表某个操作，例如 [servers.vs28.restartwww1, servers.vs28.restartwww2] 表示包含 vs28 服务器的两个 restartwww 操作。在 Server 内的 includes 定义，可以省略写 `servers` 和 `server title`
executor: 可以提供一个 python 脚本源文件作为当前操作的执行器，FlashOps 针对这个操作将不执行任何工作，仅调用执行器，详见【自定义执行器】
```

#### 预置操作类型

##### `gitpush`

本地 git 复本的 add, commit, push 操作

```
type: gitpush
folder, 设置一个在 git 管理下的目录，FlashOps 通过 git status 命令列出可提交的文件，选择文件后将进行 add，commit 和 push
```

##### `uploadfiles`

同步项目文件到远端指定目录，需要配置参数如下

```yaml
sources: 可设置多个源目录或文件，将目录或文件同步到目标服务器的指定目录
    [source folder]: 本机源文件或目录
        [target server]: [target folder] 服务器：目录。注意，无论源是文件还是目录，目标都需要给出一个目录名，而非文件名，若目录不存在会尝试创建。也就是说在同步文件时，目的文件名是与源文件名相同的
fullordiff: full|diff。如果源是目录，可以设置同步目录全部文件，还是仅同步本地更新的文件，默认为 diff。当源是目录时，目录名以斜杠结尾表示同步目录里面的内容，不包含目录本身，当目录名不以斜杠结尾时表示同步目录本身。源目录中文件是否更新的判断依据是文件的修改时间要晚于远端此文件的修改时间，或文件大小不同。
excludes: 排除文件或目录。如果源是目录时，可以排除一些指定文件。
```

>注：上传同步文件是先用 tar 压缩打包，再上传，再解压。打包上传可以保持文件原有的修改时间，以便在同步时可以比较两端文件的修改日期，来判断文件是否相同。当文件修改日期和字节数都相同时，认定为文件相同。

##### `downfiles`

从服务器下载文件，只能作为`server`的操作。也可定义在`task`中但必须指定`target`为某个`server`。

```yaml
compress: 下载前是否压缩，针对本下载操作的所有文件有效。如果压缩，在服务器先利用 tar 压缩到 /flashops/tmp 目录中再下载。源是目录时一定会先压缩再下载。
files: 可设置多个，服务器端目录或文件:复制到本地的目标目录或文件键值对。目标是目录时，文件名与原文件相同，目标是文件时，若文件已存在会覆盖。源是目录时，目标必须是目录。源是文件时，目标可以不是文件而是目录。所以，若不改变文件名，目标总是可以写目录名。
举例如下：
  '/var/log/syslog': /Users/vs/temp # 目录下载到目录，默认压缩
  '/var/log/user.log': '/Users/vs/temp' # 文件下载到目录，将保持原文件名，可指定是否压缩
  '/var/log/user.log': '/Users/vs/temp/user_##%Y%m%d%H%M%S##.log' # 文件下载到文件，可指定是否压缩，文件名中可使用变量
```

#### YAML配置文件中的变量

变量分为两种，第一种是环境变量，或需要用户输入而提供的变量

- 使用 Jinja2 变量语法，即 {{variant_name}} ，注意书写时需要用单引号或双引号将整个字符串括起来，否则解析 yaml 时会遇到错误
- 全大写变量为全局公用变量
    - CLIPBOARD，系统剪切板内容
    - 其它，首先从系统环境变量中取同名变量，若无值，要求用户输入，且在整个 flashops 运行期间只输入一次
- 除全大写以外为普通变量，在运行时根据需要要求用户输入，并且每次运行都需要输入，而不像全局变量那样只需输入一次
- 变量名为字符、数字、下划线组合，不可以有空格
- 变量名若包含 pass 字样，会以密码的形式输入，即在终端输入时屏幕上不回显输入内容
- 在一个批次内的所有操作的所有命令，同名变量只需要输入一次

第二种是日期时间变量，里面写 python 的日期格式化字符串

- 使用双井号把变量括起来，例如`##%Y%m%d##`

#### 服务器上的flashops目录

由于同步文件的需要，FlashOps 会在服务器上创建 /flashops 目录，其中包含几个子目录

- upcache, 转存上传同步文件时的压缩文件
- tmp, 可以存储临时文件


### 自定义执行器

必须是一个 python 脚本源文件。FlashOps 将脚本用`exec`执行，提供环境如下：

```
# 这里的对象指 server/project/task，针对 server 有一个属性 _conn_ 是 Fabric.Connection 的实例，针对 project 有一个属性 _conn_ 是 invoke 模块
{
   "operation": 当前操作,
   "objhost": 定义这个操作的对象,
   "objtarget": 操作要执行的目标对象,
   "get_obj_by_title": 根据 [servers.|projects.]title 得到对象,
   "get_obj_and_operation": 根据 [servers|projects|task].[title].[operation title] 得到对象和操作,
   "fill_vars": 填充字符串中的变量，若需要用户提供变量值，会提示输入,
   "K_DIR_HOME": FlashOps 在服务器上的目录，即 /flashops
}
```

### 运行

    $ flashops
    Hi, flashops
    No config file provided, using FLASHOPS_FILE. -h to see the help.
    File: /Users/mike/demo.yaml
    [f] Files
    [r] Projects
    [s] Servers
    [t] Tasks
    [c] Statements
    [D] Donation
    Please input your choice ("exit" for quit):

> 不带任何参数运行时，默认使用系统环境变量`FLASHOPS_FILE`指定的配置文件。或可使用`-f`参数指定配置文件名，更多选项可查看帮助。

或者：

  $ python -m flashops

### 交互下的一些有用命令

- `/`，回到根
- `.`，回到上一级
- `?`，查看当前可执行的操作
- `?`+`序号`或`快捷键`，查看指定条目的定义
- `test:`+`序号`或`快捷键`，查看指定任务或操作将会执行的命令，对预置类型的命令不完全有效，例如上传文件，因为打包和上传等工作不是通过 shell 命令实现的
- `/reload`，重新加载当前配置文件内容，当你修改了配置文件时，不需要退出 flashops ，只需要重新加载即可

## 捐赠

### 支付宝

提示：别忘了先领红包哦~

![](images/alipay_hb.png)&nbsp;　　　　&nbsp;![](images/alipay_qr.png)

### Paypal

https://www.paypal.me/dongyg
