# 运行

无参数，尝试使用用户目录下的 flashops.yml 或 flashops.yaml

	$ flashops
	Hi, flashops
	No config file provided, using default. -h to see the help.
	/Users/mike/flashops.yaml not exists!

查看使用帮助

	$ flashops -h
	Hi, flashops
	usage: flashops [-h] [-f FILE] [-v] [-e ENV] [-t]

	optional arguments:
	  -h, --help            show this help message and exit
	  -f FILE, --file FILE  Indicate YAML config file, otherwise:
	                        $HOME/flashop.yaml
	  -v, --version         Show Version
	  -e ENV, --env ENV     Indicate environment variables (eg: WORKDIR=/mywork;)
	  -t, --test            Test environment

查看版本

	$ flashops -v
	Hi, flashops
	FlashOps Version: 18.12.317

进入 flashops

	$ flashops -f demo.yaml
	Hi, flashops
	File: /Users/mike/fops/demo.yaml
	[f] Files
	[r] Projects
	[s] Servers
	[t] Tasks
	[c] Statements
	[D] Donation
	Please input your choice ("exit" for quit):

传入环境变量

	$ flashops -f demo.yaml -e "WORK_PATH=/Users/mike/projects"
	Hi, flashops
	File: /Users/mike/fops/demo.yaml
	[f] Files
	[r] Projects
	[s] Servers
	[t] Tasks
	[c] Statements
	[D] Donation
	Please input your choice ("exit" for quit): env work
	WORK_PATH=/Users/mike/projects

# 配置

## 连接到 Docker 默认虚拟机

	servers:
	  - title: Docker Machine Default
	    ssh:
	      host: 192.168.99.100
	      user: docker
	      keyfile: /Users/mike/.docker/machine/machines/default/id_rsa

> 可以看到，你可以通过给定`keyfile`连接到服务器

## 提交本地 git 仓库

	projects:
	  - title: A Web Project
	    operations:
	      - title: Push source code
	        type: gitpush
	        folder: '{{WORK_PATH}}/www'

> 配置中存在变量的时候，像上面的`{{WORK_PATH}}`，整个字符串用引号括起来。

## 同步本地文件到服务器

	projects:
	  - title: A Web Project
	    operations:
	      - title: Upload Production Config
	        type: uploadfiles
	        issudo: True
	        sources:
	          '{{WORK_PATH}}/www/cfg/':
	            server01: '{{SERVER_ROOT}}/docker/www/cfg/'

> 你可以在本地编辑代码、配置文件等，然后通过同步到远端的方法发布你的软件到服务器上

## 组合操作实现一键发布

	projects:
	  - title: A java Project
	    operations:
	      - title: Build
	        commands: [ 'cd {{WORK_PATH}}/myadmin && ant' ]
	      - title: Deploy
	        type: uploadfiles
	        issudo: True
	        sources:
	          '{{WORK_PATH}}/myadmin/dist/myadmin.war':
	            server02: '{{SERVER_ROOT}}/docker/myadmin/webapps/'
	      - title: Build and Deploy
	        includes: [ 'Build', 'Deploy' ]

> 你可以将`构建`和`发布`这两个操作组合在一起

## 组合操作实现实现一键复制表

	servers:
	  - title: server03
	    ssh:
	      host: 192.168.99.102
	      user: mike
	    operations:
	      - title: Export Table
	        commands: ['mysqldump -h 127.0.0.1 -P 3306 -u root --password={{MYSQL_PASS}} -p demodb {{table_name}} > /flashops/tmp/export_{{table_name}}_##%Y%m%d##.sql']
	tasks:
	  - title: Copy Table from server03
	    operations:
	      - title: Export
	        includes: ['servers.server03.Export Table']
	      - title: Download
	        target: servers.server03
	        type: downfiles
	        compress: False
	        files:
	          '/flashops/tmp/export_{{table_name}}_##%Y%m%d##.sql': /Users/mike/temp
	      - title: Import
	        target: 'projects.A Web Project'
	        commands: ['mysql -h 192.168.99.100 -P 3306 -u root -p demodb --password=123456 < /Users/mike/temp/export_{{table_name}}_##%Y%m%d##.sql']

> 注意：在`tasks`中的操作，不是`includes`的而是具体定义的操作，都需要给出`target`来告知程序这个操作是在哪里执行的。

## 下载文件

> 上面已经演示了使用`downfiles`操作类型下载文件。如果你愿意，你也完全可以自己写命令实现下载文件，像下面这样。

	projects:
	  - title: A web Project
	    operations:
	      - title: Download log
	        commands: [ 'scp mike@server01:/flashops/logs/nginx_access_20190101.log /Users/mike/temp/' ]

