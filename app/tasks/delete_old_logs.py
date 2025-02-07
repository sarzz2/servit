import os
from datetime import datetime, timedelta

from celery import shared_task

LOGS_DIR = "./logs"


@shared_task
def delete_old_logs():
    """Deletes log files older than 30 days"""
    cutoff_date = datetime.now() - timedelta(days=30)

    for log_file in os.listdir(LOGS_DIR):
        if log_file.startswith("application_dev_"):
            # Extract the date from the filename
            date_part = log_file.replace("application_dev_", "")
            date_part = date_part.replace(".log", "")
            try:
                log_date = datetime.strptime(date_part, "%d%m%Y")
                if log_date < cutoff_date:
                    os.remove(os.path.join(LOGS_DIR, log_file))
                    print(f"Deleted old log file: {log_file}")
            except ValueError:
                continue
