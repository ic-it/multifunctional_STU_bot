import inspect
import time

def func_cooldown(cd: int = 0) -> int:
    """ Decorator for functions that should be called only once in a given time period. """
    
    def decorator(func):
        func._last_call = 0
        
        if inspect.iscoroutinefunction(func):
            async def wrapper(*args, **kwargs):
                if time.time() - func._last_call > cd:
                    func._last_call = time.time()
                    return await func(*args, **kwargs)
                return 
        else:
            def wrapper(*args, **kwargs):
                if time.time() - func._last_call > cd:
                    func._last_call = time.time()
                    return func(*args, **kwargs)
                return None
        return wrapper
    return decorator