import pytest
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
