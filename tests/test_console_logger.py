import logging

from tests.helpers.capture_logging import catch_logs, records_to_tuples


class TestLogger:
    def test_console_logger(self):
        try:
            from ccdcoe.loggers.console_logger import ConsoleLogger

            logging.setLoggerClass(ConsoleLogger)

            logger_name = "TEST_CONSOLE_LOGGER"
            logger = logging.getLogger(logger_name)
            logger.propagate = True

            with catch_logs(level=logging.DEBUG, logger=logger) as handler:
                logger.debug("Debug message")
                logger.info("Info message")
                logger.warning("Warning message")
                logger.error("Error message")
                logger.critical("Critical message")
                assert records_to_tuples(handler.records) == [
                    (logger_name, logging.DEBUG, "\x1b[35m[D] Debug message\x1b[0m"),
                    (logger_name, logging.INFO, "\x1b[37m[+] Info message\x1b[0m"),
                    (
                        logger_name,
                        logging.WARNING,
                        "\x1b[33m[*] Warning message\x1b[0m",
                    ),
                    (logger_name, logging.ERROR, "\x1b[31m[!] Error message\x1b[0m"),
                    (
                        logger_name,
                        logging.CRITICAL,
                        "\x1b[31m[!!] Critical message\x1b[0m",
                    ),
                ]

        except Exception:
            raise
