import logging
import os
import shutil

from tests.helpers.capture_logging import catch_logs, records_to_tuples


class TestLogger:
    def test_app_logger(self):
        try:
            from ccdcoe.loggers.app_logger import AppLogger

            logging.setLoggerClass(AppLogger)

            logger_name = "TEST_APP_LOGGER"
            logger = logging.getLogger(logger_name)
            logger.propagate = True

            with catch_logs(level=logging.DEBUG, logger=logger) as handler:
                logger.debug("Debug message")
                logger.info("Info message")
                logger.warning("Warning message")
                logger.error("Error message")
                logger.critical("Critical message")
                assert records_to_tuples(handler.records) == [
                    (logger_name, logging.DEBUG, "\x1b[35mDebug message\x1b[0m"),
                    (logger_name, logging.INFO, "\x1b[37mInfo message\x1b[0m"),
                    (logger_name, logging.WARNING, "\x1b[33mWarning message\x1b[0m"),
                    (logger_name, logging.ERROR, "\x1b[31mError message\x1b[0m"),
                    (logger_name, logging.CRITICAL, "\x1b[31mCritical message\x1b[0m"),
                ]

        except Exception:
            raise

    def test_handler_types(self):
        os.environ["LOG_FILE_PATH"] = "./tests/test_data/should_not_be_there"

        from ccdcoe.loggers.app_logger import AppLogger
        from logging.handlers import RotatingFileHandler

        logging.setLoggerClass(AppLogger)

        logger = logging.getLogger("test_handler_types")

        assert len(logger.handlers) == 2
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert isinstance(logger.handlers[1], RotatingFileHandler)

        shutil.rmtree("./tests/test_data/should_not_be_there")
