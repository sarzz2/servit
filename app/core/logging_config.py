import json
import logging
import sys
from logging.handlers import SocketHandler

import colorlog

LOGSTASH_HOST = "localhost"
LOGSTASH_PORT = 5000


class LogstashFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "message": record.getMessage(),
            "log_level": record.levelname,
            "logger_name": record.name,
            "filename": record.filename,
            "line_number": record.lineno,
            "function_name": record.funcName,
            "process_name": record.processName,
            "thread_name": record.threadName,
        }
        return json.dumps(log_record)


def configure_logging():
    logger = logging.getLogger("fastapi")
    logger.setLevel(logging.DEBUG)

    # Configure colorlog for console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)s:     %(message)s",
        log_colors={
            "DEBUG": "bold_blue",
            "INFO": "bold_green",
            "WARNING": "bold_yellow",
            "ERROR": "bold_red",
            "CRITICAL": "bold_purple",
        },
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Configure socket handler for Logstash
    socket_handler = SocketHandler(LOGSTASH_HOST, LOGSTASH_PORT)
    socket_formatter = LogstashFormatter()
    socket_handler.setFormatter(socket_formatter)
    logger.addHandler(socket_handler)

    return logger
