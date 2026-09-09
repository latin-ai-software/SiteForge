"""Tools package for latinmagazine update server utilities.

Providing an explicit package file so WSGI servers can reliably import
`tools.update_server` when started with different PYTHONPATH/workdir settings.
"""

__all__ = ["update_server"]
