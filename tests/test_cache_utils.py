import pytest
from unittest.mock import MagicMock
from lib.cache_utils import get_cache_stats, clear_all_caches, cache_api_response


def test_cache_stats_returns_dict_when_cache_unavailable():
    """Test that get_cache_stats returns error dict if cache unavailable"""
    stats = get_cache_stats()
    assert isinstance(stats, dict)


def test_clear_all_caches_does_not_crash():
    """Test that clear_all_caches can be called safely"""
    try:
        clear_all_caches()
        assert True
    except Exception:
        pytest.fail("clear_all_caches raised an exception")


def test_cache_api_response_decorator():
    """Test cache_api_response decorator without external cache"""
    call_count = 0
    
    @cache_api_response('test_key', ttl=300)
    def test_func():
        nonlocal call_count
        call_count += 1
        return {'result': 'data'}
    
    result1 = test_func()
    result2 = test_func()
    
    assert result1 == result2
    assert result1 == {'result': 'data'}


def test_cache_db_query_decorator_uses_db_cache_when_available(monkeypatch):
    import lib.cache_utils as cache_utils

    fake_db_cache = MagicMock()
    fake_db_cache.get.return_value = None
    fake_db_cache.set = MagicMock()

    monkeypatch.setattr(cache_utils, 'CACHE_AVAILABLE', True)
    monkeypatch.setattr(cache_utils, 'db_cache', fake_db_cache)

    @cache_utils.cache_db_query('test_db_key', ttl=123)
    def test_db_func():
        return 42

    assert test_db_func() == 42
    fake_db_cache.set.assert_called_once_with('test_db_key', 42, ttl=123)

    fake_db_cache.get.return_value = 42
    assert test_db_func() == 42
    assert fake_db_cache.get.call_count >= 2


def test_invalidate_cache_clears_matching_entries(monkeypatch):
    import lib.cache_utils as cache_utils

    fake_cache = MagicMock()
    fake_cache.keys.return_value = ['user:1', 'user:2', 'other:1']
    fake_cache.delete = MagicMock()

    monkeypatch.setattr(cache_utils, 'CACHE_AVAILABLE', True)

    cache_utils.invalidate_cache(fake_cache, key_pattern='user:*')

    fake_cache.delete.assert_any_call('user:1')
    fake_cache.delete.assert_any_call('user:2')
    assert fake_cache.delete.call_count == 2


def test_invalidate_cache_clears_all_caches_when_no_instance(monkeypatch):
    import lib.cache_utils as cache_utils

    fake_general = MagicMock()
    fake_api = MagicMock()
    fake_db = MagicMock()
    fake_view = MagicMock()

    monkeypatch.setattr(cache_utils, 'CACHE_AVAILABLE', True)
    monkeypatch.setattr(cache_utils, 'general_cache', fake_general)
    monkeypatch.setattr(cache_utils, 'api_cache', fake_api)
    monkeypatch.setattr(cache_utils, 'db_cache', fake_db)
    monkeypatch.setattr(cache_utils, 'view_cache', fake_view)

    cache_utils.invalidate_cache()

    fake_general.clear.assert_called_once()
    fake_api.clear.assert_called_once()
    fake_db.clear.assert_called_once()
    fake_view.clear.assert_called_once()
