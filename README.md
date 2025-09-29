# CCDCOE package

[![GitHub Release](https://img.shields.io/github/release/ccdcoe/ccdcoe.svg?style=flat)]()
[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)

![pypi](https://github.com/ccdcoe/ccdcoe/actions/workflows/package_to_pypi.yaml/badge.svg)

This package contains generic re-usable code.

Install the full package:

```
pip install ccdcoe[all]
```

Package has several modules which can be installed separately by specifying them 
as an extra requirement. To install the http_apis module only, specify:

```
pip install ccdcoe[http_apis]
```
Or for multiple modules:
```
pip install ccdcoe[http_apis, loggers]
```

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
