from datetime import datetime, timedelta
from functools import wraps

_cache = {}
CACHE_TTL = 300

def cached(ttl=CACHE_TTL):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}_{args}_{kwargs}"
            
            if key in _cache:
                data, timestamp = _cache[key]
                if datetime.now() - timestamp < timedelta(seconds=ttl):
                    print(f"   📦 Кэш: {func.__name__}")
                    return data
            
            result = func(*args, **kwargs)
            _cache[key] = (result, datetime.now())
            return result
        return wrapper
    return decorator

def clear_cache():
    global _cache
    _cache.clear()
    print("✅ Кэш очищен")

def clear_user_cache(user_id):
    keys_to_delete = [k for k in _cache.keys() if str(user_id) in k]
    for key in keys_to_delete:
        del _cache[key]
    print(f"✅ Очищен кэш для пользователя {user_id}")