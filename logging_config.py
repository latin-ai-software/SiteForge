import logging
import sys
from pathlib import Path

def setup_logging(app):
    """Setup structured logging for the application."""

    # Create logs directory if it doesn't exist
    log_dir = Path(app.root_path) / 'logs'
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / 'app.log'),
        ]
    )

    # Set specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

    # Add request logging
    @app.before_request
    def log_request_info():
        from flask import request
        app.logger.info(f'{request.method} {request.url} - {request.remote_addr}')

    @app.after_request
    def log_response_info(response):
        app.logger.info(f'Response: {response.status_code}')
        return response

    # Log unhandled exceptions
    @app.errorhandler(Exception)
    def log_exception(error):
        app.logger.error(f'Unhandled exception: {error}', exc_info=True)
        # Re-raise to let Flask handle it
        raise error

    return app