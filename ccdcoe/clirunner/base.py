import logging
import subprocess
from typing import List

from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)


class BaseCLIRunner(object):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._parent_cmd = "docker"

    @property
    def parent_cmd(self) -> str:
        return self._parent_cmd

    def _call_cmd(self, arguments: List[str] = ()) -> List[str]:
        return [arg for arg in ([self.parent_cmd] + list(arguments)) if arg]

    def call(
        self,
        *args: str,
        stdin=None,
        stdout=None,
        stderr=None,
        **kwargs,
    ) -> subprocess.CompletedProcess:
        """
        Call 'self._parent_cmd' with the generated command
        """
        cmd = self._call_cmd(args)
        self.logger.info(f"# {' '.join(cmd)}")
        p = subprocess.run(
            cmd, stdin=stdin, stdout=stdout, stderr=stderr, **kwargs, text=True
        )
        self.logger.debug(f"Returned from {cmd[0]}: {p.returncode}")
        return p

    def __repr__(self):
        return f"<{self.__class__.__name__}>"
