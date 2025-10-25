# CCDCOE package

[![GitHub Release](https://img.shields.io/github/release/ccdcoe/ccdcoe.svg?style=flat)]()
[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)

![pypi](https://github.com/ccdcoe/ccdcoe/actions/workflows/package_to_pypi.yaml/badge.svg)

This package contains generic re-usable code.

Install the full package:

```
pip install ccdcoe[all]
```

This package has several modules which can be installed separately by specifying them 
as an extra requirement. To install the http_apis module only, specify:

```
pip install ccdcoe[http_apis]
```
Or for multiple modules:
```
pip install ccdcoe[http_apis, loggers]
```

## Command line interface

The ccdcoe package contains a cli application for providentia/gitlab communication and controlling the vm deployment
pipelines; if this is the only thing you would like to use from the package please run:

```
pip install ccdcoe[cli_code]
```

After the installation run `ccdcoe` from the command line and have a look at the help section for the available
commands.

The settings for the cli are controlled from a `.env` file located at `~/.ccdcoe/.env` and has the following 
defaults which are put there when you first run the application:

```bash
TRIGGER_TOKEN=<<MANDATORY_VALUE>>
PAT_TOKEN=<<MANDATORY_VALUE>>
GITLAB_URL=<<MANDATORY_VALUE>>
NEXUS_HOST=<<MANDATORY_VALUE>>
PROVIDENTIA_URL=<<MANDATORY_VALUE>>
PROVIDENTIA_TOKEN=<<MANDATORY_VALUE>>
PROJECT_ROOT=<<MANDATORY_VALUE>>
PROJECT_VERSION=<<MANDATORY_VALUE>>
```

These settings are, like you can see, all mandatory. Consult `ccdcoe/deployments/deployment_config.py` for more, 
optional, settings. 

The CLI application supports tab completion; for bash add `eval "$(_CCDCOE_COMPLETE=bash_source ccdcoe)"` to your 
.bashrc to activate the tab completion. 
Or you could save the output of the following command as a script somewhere 
`_FOO_BAR_COMPLETE=bash_source foo-bar > ~/.foo-bar-complete.bash` and source that file in your .bashrc like so: 
`. ~/.foo-bar-complete.bash`

Other shells (Zsh, Fish) are supported as well; please check the 
[click documentation](https://click.palletsprojects.com/en/stable/shell-completion/)

### Examples

Example for BT28, deploying up to tier 7 on branch cicd-update:

```bash
ccdcoe deploy tier --level 7 -b cicd-update -t 28
```

Example for BT24, deploying just tier 4 on branch cicd-update:

```python
ccdcoe deploy tier --limit 4 -b cicd-update -t 24
```

You can exclude hosts from the pipeline deployment:

```python
ccdcoe deploy tier --limit 4 -t 24 --skip_hosts host1,host2,host3
```

^ Will deploy tier4 for BT24 **except** host1,host2,host3

Or you can deploy only some selected hosts:

```python
ccdcoe deploy tier --limit 4 -t 24 --only_hosts host1,host2,host3
```

^ Will deploy **only** host1,host2,host3 from tier4 for BT24

## Adding modules and/or groups

Everything for this package is defined in the pyproject.toml file. Dependencies are managed by poetry and grouped in, you guessed it, groups. Every poetry group can be installed as an extra using pip. 

Extra extras or group on group/extra dependencies can also be defined in the [tool.ccdcoe.group.dependencies] section. Everything defined here will also become an extra if no group already exists. You can use everything defined here as dependency for another group, order does **not** matter.

example:
```toml
[tool.ccdcoe.group.dependencies]
my_awesome_extra = ["my_awesome_group", "my_other_group"]
my_awesome_group = ["my_logging_group"]

[tool.poetry.group.my_awesome_group.dependencies]
<dependency here>

[tool.poetry.group.my_other_group.dependencies]
<dependency here>

[tool.poetry.group.my_logging_group.dependencies]
<dependency here>
```

Using this example the following extras exist with the correct dependencies:
```
pip install ccdcoe[all]
pip install ccdcoe[my-awesome-extra]
pip install ccdcoe[my-awesome-group]
pip install ccdcoe[my-other-group]
pip install ccdcoe[my-logging-group]
```

## Modules

The following modules are available in the ccdcoe package:

* http_apis
* loggers
* dumpers
* deployments
* cli
* redis_cache
* flask_managers
* flask_middleware
* flask_plugins
* auth
* sso
* plugins
* sql_migrations

### HTTP apis

Baseclass for http api communication is present under 
ccdcoe.http_apis.base_class.api_base_class.ApiBaseClass

### Loggers

There are three loggers provided:
* ConsoleLogger (ccdcoe.loggers.app_logger.ConsoleLogger)
* AppLogger (ccdcoe.loggers.app_logger.AppLogger)
* GunicornLogger (ccdcoe.loggers.app_logger.GunicornLogger)

The ConsoleLogger is intended as a loggerClass for cli applications.

The AppLogger is intended to be used as a loggerClass to be used for the 
standard python logging module.

```python
import logging
from ccdcoe.loggers.app_logger import AppLogger

logging.setLoggerClass(AppLogger)

mylogger = logging.getLogger(__name__)
```
The 'mylogger' instance has all the proper formatting and handlers 
(according to the desired config) to log messages.

The Gunicorn logger is intended to be used for as a loggerClass for the 
gunicorn webserver; it enables the FlaskAppManager to set the necessary 
formatting and handles according to the AppLogger specs and a custom format
for the gunicorn access logging.

### Flask app manager

The FlaskAppManager is intended to be used to 'run' flask applications in 
both test, development as in production environments. 

```python
from YADA import app
from ccdcoe.flask_managers.flask_app_manager import FlaskAppManager

fam = FlaskAppManager(version="1.0", app=app)
fam.run()
```
Depending on the configuration the FlaskAppManager uses a werkzeug (DEBUG == True)
or a gunicorn webserver. TLS could be set for both webservers iaw the module specific
README.md.

### SQL Migrations

The sql migrations can be used to facilitate migration between different
versions of sql models / versions. It relies on flask migrate to perform
the different migrations. It has a CLI as well as an python class based API.

Check the command line help
```
python3 -m ccdcoe.sql_migrations.flask_sql_migrate -a /path/to/script_with_flask_app.py -i
python3 -m ccdcoe.sql_migrations.flask_sql_migrate -a /path/to/script_with_flask_app.py -m
python3 -m ccdcoe.sql_migrations.flask_sql_migrate -a /path/to/script_with_flask_app.py -u
```

Or initiate the FlaskSqlMigrate as a class and initiate the migration 
process from there: 
```python
from ccdcoe.sql_migrations.flask_sql_migrate import FlaskSqlMigrate
fsm = FlaskSqlMigrate(app_ref="/path/to/script_with_flask_app.py")

fsm.db_init()
fsm.db_migrate()
fsm.db_update()
```
