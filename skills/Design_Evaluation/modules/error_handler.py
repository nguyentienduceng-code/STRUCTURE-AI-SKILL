import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import logging
from functools import wraps
import os

class StructuralAILogger:
    _instance = None
    
    def __new__(cls, log_dir="logs/"):
        if cls._instance is None:
            cls._instance = super(StructuralAILogger, cls).__new__(cls)
            cls._instance.logger = logging.getLogger("StructuralAI")
            
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            handler = logging.FileHandler(f"{log_dir}/system.log", encoding='utf-8')
            handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)s | %(module)s | %(message)s'
            ))
            
            if not cls._instance.logger.handlers:
                cls._instance.logger.addHandler(handler)
            cls._instance.logger.setLevel(logging.INFO)
            
        return cls._instance

def with_error_handling(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Lấy đường dẫn thư mục gốc (g:\My Drive\Google AI Studio\.agents)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            agents_dir = os.path.dirname(current_dir)
            log_dir = os.path.join(agents_dir, "logs")
            
            logger = StructuralAILogger(log_dir=log_dir).logger
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            print(f"❌ Python Runtime Error in {func.__name__}: {str(e)}. Xem logs/system.log để biết thêm chi tiết.")
            return {"error": str(e), "function": func.__name__}
    return wrapper
