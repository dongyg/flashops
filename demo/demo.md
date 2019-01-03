# Run flashops

No parameters, will try flashops.yml or flashops.yaml in the user home directory

	$ flashops
	Hi, flashops
	No config file provided, using default. -h to see the help.
	/Users/mike/flashops.yaml not exists!

Show help

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

Show version

	$ flashops -v
	Hi, flashops
	FlashOps Version: 18.12.317

Run

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

Pass environment variables

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

# Configuration

## Connect to Docker Machine

	servers:
	  - title: Docker Machine Default
	    ssh:
	      host: 192.168.99.100
	      user: docker
	      keyfile: /Users/mike/.docker/machine/machines/default/id_rsa

> In this case, we use the Docker Machine's SSH certificate

## Commit and Push a git repository

	projects:
	  - title: A Web Project
	    operations:
	      - title: Push source code
	        type: gitpush
	        folder: '{{WORK_PATH}}/www'

> When a variable exists in the configuration like above `{{WORK_PATH}}', the entire string is enclosed in quotes.

## Sync local files to remote

	projects:
	  - title: A Web Project
	    operations:
	      - title: Upload Production Config
	        type: uploadfiles
	        issudo: True
	        sources:
	          '{{WORK_PATH}}/www/cfg/':
	            server01: '{{SERVER_ROOT}}/docker/www/cfg/'

> You can edit code, configuration files, etc. locally, and then publish your software to the server by synchronizing to the remote end.

## One-click Publishing by Composite Operations

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

> Combine `build` and `publish` operations.

## Implementing a key to replicate tables from server to local by combining operations

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

> Note: Operations in `tasks`, not `include`, but specifically defined operations, need to give `target` to inform the program where the operation is performed.

## Download files

> The downloading of files using the `downfiles` operation type has been demonstrated above. If you want, you can also write your own commands to download files, as follows.

	projects:
	  - title: A web Project
	    operations:
	      - title: Download log
	        commands: [ 'scp mike@server01:/flashops/logs/nginx_access_20190101.log /Users/mike/temp/' ]

