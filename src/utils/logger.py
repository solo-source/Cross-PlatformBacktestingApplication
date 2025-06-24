# src/utils/logger.py
"""
Centralized logging setup.
"""

import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename='app.log',
    filemode='a',
    format='%(asctime)s %(levelname)s:%(message)s'
)
logger = logging.getLogger(__name__)