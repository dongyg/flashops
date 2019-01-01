
## What's FlashOps

FlashOps (a clipped compound of "flash" and "operations") is a tool that simplifies the process of managing a Linux server through SSH. A set of operations or commands that you often perform can be simplified to just one or two characters.

Maybe you think a shell script is good way to do your work. But FlashOps can do more, like sync file between remote and your computer.

## How to get

FlashOps is written in Python and supports both python2 and python3, requires [Fabric](https://pypi.org/project/Fabric/), [YAML](https://pypi.org/project/PyYAML/), etc. You can simply install it using pip.

```
pip install flashops
```


## How to use

### Precondition

FlashOps uses Fabric to manage remote Linux servers via ssh. Before using FlashOps, make sure you can connect and manage your Linux server via ssh.

### Terms

FlashOps defines four types of work:

- projects
- servers
- tasks
- statements

#### Operations

`Operation` is the smallest unit of work, which can be defined in projects, servers, tasks. An operation can be a series of shell statements, or a program that can be executed or called under the shell. It can be a combination of several other operations. In addition, FlashOps provides some preset types of operations.

### How to config

FlashOps uses the yaml format file as a configuration file, and everything is written in the yaml file.

```yaml
- projects
    - title
    - operations
- servers
    - title
    - ssh, parameters to connect to the server via ssh
        - host
        - port
        - user
        - sudopass
        - keyfile
        - keypass
    - operations
- tasks, combine multiple actions defined in a project or server, or you can define the operation directly
    - title
    - operations
- statements。Strings such as commands or statements that are often used. It can be quickly listed and filtered, you can copy it and use it.
```

#### Parameters of operation

```yaml
title: the title of the operation
type: see [Built-in Operation Type], if not given, [commands] give the command to be executed
commands: one or more shell commands or scripts that can be executed under the shell
issudo: indicates whether to execute the command using sudo mode for server
yesorno: whether to ask to continue before execution
target: in [tasks] section, when you define a operation directly instead of [includes], indicates the target (server/project) by [servers.|projects.]title
visible: if the main purpose of an operation is to be used in [includes], you can set visible to Flase. However, it still occupies the serial number
shortcut: shortcut key, if it conflicts with other operation sequence numbers, it will be invalid
includes: to include other operations instead of [commands] by `[servers|projects.][server title|project title.]operation title`
executor: a python script source file as the executor of the current operation, see [Custom Executor]
```

#### Built-in Operation Type

##### `gitpush`

Add, commit, push operations for local git repository.

```yaml
type: gitpush
folder: a folder of local git repository. FlashOps lists the files through [git status] command, you can choose files and add, commit, push
```

##### `uploadfiles`

Synchronize local files to the remote.

```yaml
sources: one or more files or directories you want to synchronize
    [source]: a file or a directory in local machine
        [target server]: [target folder]
fullordiff: full|diff. Indicates full copy or diff copy when the [source] is a directory.
excludes: Excludes some files when  the [source] is a directory.
```

##### `downfiles`

Download files from remote.

```yaml
compress: Whether to compress before downloading
files: a map of [remote file or directory - a local file or directory]. For example
  '/var/log/syslog': /Users/mike/temp Download a directory to a directory
  '/var/log/user.log': '/Users/mike/temp' Download a file to a directory
  '/var/log/user.log': '/Users/mike/temp/user_##%Y%m%d%H%M%S##.log' Download a file to a file
```

#### Variables in the configuration file

Environmental variables

- Use Jinja2 syntax {{variant_name}}. Notice if the variable is at the beginning of the content, you need to use single or double quotes, otherwise you will encounter errors when parsing yaml
- Variables with all uppercase letters are global public variables
    - CLIPBOARD, System clipboard content
    - Others, First, find the same name variable from the system environment variable. If there is no value, a input is required, and only once during the entire flashops session.
- It is a normal variable except for all uppercase. It requires user input at runtime and needs input every time it runs.
- The variable name is a combination of characters, numbers, and underscores. There can be no spaces.
- If the variable name contains the word `pass`, it will be entered as a password, that is, the input content will not be echoed on the screen.
- the same name variable only needs to be entered once for all commands of all operations in a batch. That is very useful, for example, you can:
    - export a table from remote database, save it to a file, and the table name is a variable
    - download the file
    - import the talbe data into local database

Datetime variables, a date format string of python.

- Enclose the variables with a double `#`, like: `##%Y%m%d##`

#### The flashops directory in remote

Due to the need to synchronize files, FlashOps creates a /flashops directory on the server with several subdirectories. You can delete the files in those directories when you don't need them.

### Custom Executor

Must be a python script. FlashOps executes the script with `exec`, providing arguments as follows:

```
# object: means a server/project/task. It has a member _conn_ which is a instance of Fabric.Connection when it is a server, or which is the invoke module when it is a project.
{
   "operation": the operation of this executor,
   "objhost": the object of this operation,
   "objtarget": the target object given by target statement,
   "get_obj_by_title": a function can return the object by parameter: [servers.|projects.]title,
   "get_obj_and_operation": a function can return the object by parameter: [servers|projects|task].[title].[operation title],
   "fill_vars": fill the variables in the string, if the variable value needs to provided, a prompt will show,
   "K_DIR_HOME": this is /flashops directory in remote
}
```


### Others

There are some useful commands in

- `/`, back to root
- `.`, back to parent
- `?`, list the currently executable actions
- `?`+`no.`or`shortcut`, show the defination of current item
- `test:`+`no.`or`shortcut`, show the shell commands to be executed


## Donation

### Alipay

提示：别忘了先领红包再付款哦~

![](alipay_hb.png)&nbsp;　　　　&nbsp;![](alipay_qr.png)

### Paypal

https://www.paypal.me/dongyg
