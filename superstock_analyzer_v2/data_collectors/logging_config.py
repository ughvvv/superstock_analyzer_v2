import logging

def configure_logging():
    """Configure logging with reduced output."""
    logging.getLogger('data_collectors').setLevel(logging.WARNING)
    
    # Specific logger configurations
    loggers_config = {
        'data_collectors.market_data_collector': logging.WARNING,
        'data_collectors.base_collector': logging.ERROR,
        'data_collectors.cache_manager': logging.ERROR,
        'data_collectors.rate_limiter': logging.WARNING,
        'data_collectors.qualitative_analysis': logging.WARNING
    }
    
    for logger_name, level in loggers_config.items():
        logging.getLogger(logger_name).setLevel(level)

    # Configure format to be minimal but informative
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    
    # Configure handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []  # Remove existing handlers
    root_logger.addHandler(handler)
