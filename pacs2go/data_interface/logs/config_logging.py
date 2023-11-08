import datetime
import logging
import threading
import psycopg2
import schedule
import time
from dotenv import load_dotenv
from pacs2go.data_interface.tests.test_config import (DATABASE_HOST,
                                                      DATABASE_PORT)
import os

load_dotenv()

class PostgreSQLHandler(logging.Handler):
    def __init__(self):
        super().__init__()

        self.conn = psycopg2.connect(
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB")
        )

        self.table_name = "pacs_logs"
        self.create_log_table()
        self.log_queue = []

        # Write logs to db every day at 4am
        schedule.every().day.at("04:00").do(self.save_db)
        # Clean up logs every month on the 1st day at 5:00 AM
        schedule.every(30).days.at("03:00").do(self.cleanup_logs)

        # Start the scheduler in a separate thread
        self.schedule_thread = threading.Thread(target=self.run_schedule)
        self.schedule_thread.daemon = True
        self.schedule_thread.start()

    def emit(self, record):
        self.log_queue.append(record)

    def create_log_table(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ,
                    log_message TEXT,
                    log_level TEXT
                )
            """)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = "Log table could not be created."
            raise Exception(msg)

    def write_queued_logs(self):
        if self.log_queue:
            try:
                cursor = self.conn.cursor()
                for record in self.log_queue:
                    record_timestamp = datetime.datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute(
                        f"INSERT INTO {self.table_name} (timestamp, log_message, log_level) VALUES (%s, %s, %s)",
                        (record_timestamp, record.msg, record.levelname)
                    )
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                print(f"Error in PostgreSQLHandler: {str(e)}")
    
    def cleanup_logs(self):
        # Calculate the date one year ago 
        one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)

        # Clean up logs in the database (one year old)
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE timestamp < %s",
                (one_year_ago,)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error cleaning up logs in PostgreSQLHandler: {str(e)}")

        # Clean up logs in the log file
        log_file = 'pacs2go/data_interface/logs/log_files/data_interface.log'
        try:
            with open(log_file, 'r+') as file:
                lines = file.readlines()
                file.seek(0)
                start_line = None
                for line_no, line in enumerate(lines):
                    if not start_line:
                        # Retrieve timestamp if log-file entry
                        if "|" in line.lower():
                            log_time_str = line.split('|')[0].strip()
                            log_time = datetime.datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S')
                            
                            # Check if older than one year
                            if log_time >= one_year_ago:
                                # First match that is within the past year -> save all other lines after this line
                                file.write(line)
                                start_line = line_no
                    else:
                        file.write(line)
                file.truncate()
        except Exception as e:
            print(f"Error cleaning up logs in log file: {str(e)}")

    # https://stackoverflow.com/questions/52040070/run-schedule-function-in-new-thread
    def save_db(self):
        self.write_queued_logs()
        self.log_queue = [] 

    def run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)


def get_data_interface_logger():
    # Fixed log file name
    log_file = 'pacs2go/data_interface/logs/log_files/data_interface.log'
    logger = logging.getLogger("PACS_DI_logger")
    #stops logging messages being passed to ancestor loggers
    logger.propagate = False
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)2d | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # File Handler to log to .log file
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(formatter)

    # SQL Handler to log data interface user actions to db
    db_handler = PostgreSQLHandler()
    db_handler.setFormatter(formatter)
    
    logger.addHandler(db_handler)
    logger.addHandler(file_handler)

    return logger


# Why is this done here? The answer: https://alexandra-zaharia.github.io/posts/fix-python-logger-printing-same-entry-multiple-times/
logger = get_data_interface_logger()

