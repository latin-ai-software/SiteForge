# Cache Quick Reference

## Import Cache

```python
# Use global cache instances
from lib.cache_utils import general_cache, api_cache, db_cache, view_cache

# Use data manager caches (built-in)
from lib.data.user_manager import UserManager
from lib.data.comment_manager import CommentManager
```

## Basic Operations

```python
# Set value
cache.set('key', 'value')
cache['key'] = 'value'  # Dict syntax

# Get value
value = cache.get('key')
value = cache['key']  # Dict syntax

# Delete
cache.delete('key')
del cache['key']  # Dict syntax

# Check existence
if 'key' in cache:
    print("Found")

# Get size
size = len(cache)
```

## Set with TTL

```python
# Custom TTL (seconds)
cache.set('key', 'value', ttl=300)  # 5 minutes

# Default global TTL (see lib/cache_utils.py for each cache)
cache.set('key', 'value')  # Uses cache's default TTL
```

## Get Cache Stats

```python
from lib.cache_utils import get_cache_stats

stats = get_cache_stats()
# Returns dict with: hits, misses, hit_rate, size, evictions

# Or for single cache
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}")
```

## Clear Cache

```python
from lib.cache_utils import clear_all_caches, invalidate_cache

# Clear all caches
clear_all_caches()

# Clear specific cache
cache.clear()

# Invalidate by pattern
invalidate_cache(cache, key_pattern='user:')
```

## Data Manager Caching

```python
# UserManager - automatic caching of get_all_users()
user_mgr = UserManager(base_path)
users = user_mgr.get_all_users()  # Cached
user_mgr.update_user_role('alice', 'admin')  # Auto-clears cache
user_mgr.clear_cache()  # Manual clear

# CommentManager - automatic caching of get_comments()
comment_mgr = CommentManager(base_path)
comments = comment_mgr.get_comments('post_1')  # Cached
comment_mgr.add_comment('post_1', 'john', 'text')  # Auto-clears cache
comment_mgr.clear_cache()  # Manual clear

# MediaManager - automatic caching of get_usage_summary()
media_mgr = MediaManager(base_path)
summary = media_mgr.get_usage_summary()  # Cached
media_mgr.clear_cache()  # Manual clear
```

## Decorators

```python
from lib.cache_utils import cache_api_response, cache_db_query

@cache_api_response('users_list', ttl=1800)  # 30 minutes
def get_users_from_api():
    return requests.get('https://api.example.com/users').json()

@cache_db_query('user_count', ttl=300)  # 5 minutes
def count_users():
    return db.query(User).count()
```

## Eviction Policies

- **LRU** (default): Least Recently Used - best for general use
- **FIFO**: First In First Out - simple sequential eviction
- **LFU**: Least Frequently Used - keep popular items
- **None**: Raise error when full - manual management

## Cache Sizes

- `general_cache`: 2000 entries
- `api_cache`: 1000 entries
- `db_cache`: 1000 entries
- `view_cache`: 500 entries
- Data managers: 100-1000 entries (varies)

## TTLs

- `general_cache`: 3600 seconds (1 hour)
- `api_cache`: 1800 seconds (30 minutes)
- `db_cache`: 900 seconds (15 minutes)
- `view_cache`: 3600 seconds (1 hour)
- `UserManager`: 3600 seconds (1 hour)
- `PostManager`: 1800 seconds (30 minutes)
- `CommentManager`: 900 seconds (15 minutes)
- `MediaManager`: 600 seconds (10 minutes)

## Monitoring

```python
# Flask admin route for cache stats
@admin.route('/cache/stats')
def cache_stats():
    from lib.cache_utils import get_cache_stats
    return jsonify(get_cache_stats())

# Clear cache from admin
@admin.route('/cache/clear', methods=['POST'])
def clear_cache_admin():
    from lib.cache_utils import clear_all_caches
    clear_all_caches()
    return jsonify({"status": "ok"})
```

## Performance

| Operation | Speed |
|-----------|-------|
| Cache hit | <1ms |
| Cache miss + store | ~1-5ms |
| Set | ~1µs |
| Delete | ~0.5µs |

## Key Patterns

```python
# Use prefixes for related data
cache.set('user:123:profile', data)
cache.set('user:123:settings', data)
cache.set('user:123:permissions', data)

# Invalidate all user data
for key in cache.keys():
    if key.startswith('user:123:'):
        cache.delete(key)
```

## Thread Safety

✅ All cache operations are thread-safe - no manual locking needed

## Common Issues

| Issue | Solution |
|-------|----------|
| Low hit rate | Increase cache size or TTL |
| High memory | Reduce cache sizes or TTL |
| Stale data | Lower TTL for that cache |
| Cache miss | Check key format matches |

## See Also

- [Full Integration Guide](CACHE_INTEGRATION.md)
- [Intermediarium Documentation](Intermediarium/README.md)
