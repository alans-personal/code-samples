import logging
import os
import random
import time


def configure_logging(log_file):
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Create a file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Create a formatter and set it for the file handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger


def generate_random_log_messages(logger, num_messages=10):
    for i in range(num_messages):
        # Generate a random log message
        log_level = random.choice([logging.INFO, logging.WARNING, logging.ERROR])
        log_message = f"This is a random log message {i}"
        # Log the message
        logger.log(log_level, log_message)
        time.sleep(30)  # Sleep for 30 second between messages


def main() -> None:
    """ Generate random logs """
    # Create the /local/logs directory if it doesn't exist
    log_dir = "/local/logs"
    os.makedirs(log_dir, exist_ok=True)
    # Specify the log file path
    log_file = os.path.join(log_dir, "random_logs.log")
    # Configure logging
    logger = configure_logging(log_file)
    # Generate random log messages
    generate_random_log_messages(logger)


if __name__ == "__main__":
    main()
