"""
Cache Utilities Module
======================

Provides convenient access to Intermediarium cache library with pre-configured instances
for different use cases throughout the application.

Features:
  - Global cache instances for common scenarios
  - Cache statistics tracking
  - Easy integration with Flask routes
  - Cache invalidation helpers
"""

try:
    from Intermediarium import Cache, cached, cached_method
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    print("Warning: Intermediarium cache library not found. Caching disabled.")

# Global cache instances for different purposes

# General-purpose cache (1 hour TTL)
general_cache = Cache(maxsize=2000, policy='lru', ttl=3600) if CACHE_AVAILABLE else None

# API response cache (30 minutes TTL)
api_cache = Cache(maxsize=1000, policy='lru', ttl=1800) if CACHE_AVAILABLE else None

# Database query cache (15 minutes TTL)
db_cache = Cache(maxsize=1000, policy='lru', ttl=900) if CACHE_AVAILABLE else None

# View/template cache (1 hour TTL)
view_cache = Cache(maxsize=500, policy='lru', ttl=3600) if CACHE_AVAILABLE else None


def get_cache_stats():
    """Get statistics from all cache instances"""
    if not CACHE_AVAILABLE:
        return {"error": "Cache not available"}
    
    return {
        "general_cache": general_cache.get_stats(),
        "api_cache": api_cache.get_stats(),
        "db_cache": db_cache.get_stats(),
        "view_cache": view_cache.get_stats(),
    }


def clear_all_caches():
    """Clear all cache instances"""
    if not CACHE_AVAILABLE:
        return
    
    general_cache.clear()
    api_cache.clear()
    db_cache.clear()
    view_cache.clear()


def cache_api_response(cache_key: str, ttl: int = 1800):
    """
    Decorator to cache API responses
    
    Usage:
        @cache_api_response('user_list', ttl=3600)
        def get_users():
            return fetch_users_from_api()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not CACHE_AVAILABLE:
                return func(*args, **kwargs)
            
            cached_value = api_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            api_cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


def cache_db_query(cache_key: str, ttl: int = 900):
    """
    Decorator to cache database queries
    
    Usage:
        @cache_db_query('user_count', ttl=300)
        def count_users():
            return db.query(User).count()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not CACHE_AVAILABLE:
                return func(*args, **kwargs)
            
            cached_value = db_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            db_cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


def invalidate_cache(cache_instance=None, key_pattern: str = None):
    """
    Invalidate cache entries
    
    Args:
        cache_instance: The cache to invalidate (None = invalidate all)
        key_pattern: Pattern to match keys (e.g., 'user:*' would match 'user:1', 'user:2')
    """
    if not CACHE_AVAILABLE:
        return
    
    if cache_instance is None:
        clear_all_caches()
        return
    
    if key_pattern:
        # Simple pattern matching (prefix match)
        for key in cache_instance.keys():
            if key.startswith(key_pattern.replace('*', '')):
                cache_instance.delete(key)
    else:
        cache_instance.clear()


# Example usage:
if __name__ == "__main__":
    if CACHE_AVAILABLE:
        print("Cache Stats:", get_cache_stats())
        
        # Test caching
        general_cache.set('test', 'value', ttl=60)
        print("Cached value:", general_cache.get('test'))
        
        # Show stats
        print("\nCache Statistics:")
        for name, stats in get_cache_stats().items():
            print(f"\n{name}:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
