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

## Modules

The following modules are available in the ccdcoe package:

* http_apis
* loggers
* dumpers
* deployments
* cli

### HTTP apis

Baseclass for http api communication is present under 
ccdcoe.http_apis.base_class.api_base_class.ApiBaseClass

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
