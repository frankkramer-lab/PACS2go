import logging


def db_logging():
    log_file = 'pacs2go/data_interface/logs/log_files/db.log'  # Fixed log file name
    logger = logging.getLogger("DB_logger")
    # Set level (this is the level of what will acutally be logged; rank: debug,info,warning,error,critical)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def data_interface_logger():
    log_file = 'pacs2go/data_interface/logs/log_files/data_interface.log'  # Fixed log file name
    logger = logging.getLogger("PACS_DI_logger")
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger

def xnat_wrapper_logger():
    log_file = 'pacs2go/data_interface/logs/log_files/xnat_wrapper.log'  # Fixed log file name
    logger = logging.getLogger("XNAT_Wrapper_logger")
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger