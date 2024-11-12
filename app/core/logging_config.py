import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import SocketHandler, TimedRotatingFileHandler
from queue import Queue
from threading import Thread

import colorlog

LOGSTASH_HOST = "localhost"
LOGSTASH_PORT = 5000
ENVIRONMENT = "dev"
LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file_name = f"{LOG_DIR}/application_{ENVIRONMENT}_{datetime.now().strftime('%d%m%Y')}.log"


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
    logging.getLogger("uvicorn.access").handlers.clear()
    logger.setLevel(logging.DEBUG)

    log_queue = Queue()

    # Create the console handler
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

    socket_handler = SocketHandler(LOGSTASH_HOST, LOGSTASH_PORT)
    socket_formatter = LogstashFormatter()
    socket_handler.setFormatter(socket_formatter)

    file_handler = TimedRotatingFileHandler(log_file_name, when="midnight", interval=1, backupCount=365)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)

    # Add a queue handler to the logger
    log_queue_handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(log_queue_handler)

    access_logger = logging.getLogger("uvicorn.access")
    access_logger.setLevel(logging.DEBUG)

    # Start a listener thread
    def listener():
        while True:
            record = log_queue.get()
            if record is None:
                break
            # Handle the log record in all handlers
            console_handler.handle(record)
            socket_handler.handle(record)
            file_handler.handle(record)

    listener_thread = Thread(target=listener, daemon=True)
    listener_thread.start()

    return logger
