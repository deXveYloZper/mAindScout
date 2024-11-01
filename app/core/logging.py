# app/core/logging.py

import logging
from logging.handlers import RotatingFileHandler
import os

# Determine the environment (e.g., development, production)
environment = os.getenv("ENVIRONMENT", "development")

# Create a custom logger instance
logger = logging.getLogger("my_app_logger")

# Set the logging level based on the environment
if environment == "development":
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# Create a console handler to output log messages to the terminal/console
console_handler = logging.StreamHandler()

# Create a file handler to write log messages to a file
# RotatingFileHandler automatically rotates the log file when it reaches a specified size (maxBytes).
log_file_path = os.getenv("LOG_FILE_PATH", "app.log")
file_handler = RotatingFileHandler(log_file_path, maxBytes=1000000, backupCount=5)

# Create a log message format and assign it to the handlers
# The format includes the timestamp, logger name, log level, and the actual log message.
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console_handler.setFormatter(log_format)  # Apply the format to the console handler
file_handler.setFormatter(log_format)     # Apply the format to the file handler

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Example: Add Sentry integration for production (optional)
if environment == "production":
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(
            level=logging.INFO,        # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )

        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            integrations=[sentry_logging]
        )
    except ImportError:
        logger.warning("Sentry SDK not installed, skipping Sentry integration.")
