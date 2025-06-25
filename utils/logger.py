import logging
import os
from pathlib import Path
import json

class Logger:
    _instance = None
    
    def __new__(cls, log_file='netmaptool.log', log_level='INFO'):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_file='netmaptool.log', log_level='INFO'):
        if self._initialized:
            return
            
        self.log_file = log_file
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger('netmaptool')
        self.logger.setLevel(self.log_level)
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(self.log_level)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self._initialized = True
    
    def get_logger(self):
        return self.logger
    
    def log(self, level, message, **kwargs):
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        if kwargs:
            message = f"{message} - {json.dumps(kwargs, default=str)}"
        log_func(message)

# Create a default logger instance
def get_logger():
    return Logger().get_logger()
