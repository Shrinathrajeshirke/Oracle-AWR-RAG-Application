import logging
import os
import sys
from datetime import datetime

# Calculate absolute project root: D:\Complete-GenAI\AWR-RAG-2
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Create log file with timestamp
LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
LOG_FILE_PATH = os.path.join(LOGS_DIR, LOG_FILE)

# Root logger instance
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Formatters
file_formatter = logging.Formatter("[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s")
console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Explicit File Handler (ensures the file is always created on disk)
file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

# Console Handler (for terminal display)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

# Clear existing handlers to prevent duplicate lines and attach both handlers
logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Initial confirmation log
logging.info(f"Logging initialized. Log file: {LOG_FILE_PATH}")