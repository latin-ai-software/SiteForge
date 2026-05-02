#!/usr/bin/env python3
"""
SiteForge Application Runner

This script provides a modern way to run the Flask application with proper
configuration management, logging, and deployment support.
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def create_app(config_name=None):
    """Application factory pattern."""
    from app import app

    # Apply configuration
    from config import get_config
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Setup logging
    from logging_config import setup_logging
    setup_logging(app)

    # Initialize Sentry if configured
    if app.config.get('SENTRY_DSN'):
        import sentry_sdk
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[
                sentry_sdk.integrations.flask.FlaskIntegration(),
            ],
            traces_sample_rate=1.0,
        )

    return app

def main():
    """Main entry point."""
    app = create_app()

    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')

    # Use gunicorn in production if available
    if os.environ.get('FLASK_ENV') == 'production':
        try:
            from gunicorn.app.wsgiapp import WSGIApplication
            WSGIApplication("%(prog)s [OPTIONS] [APP_MODULE]").run()
        except ImportError:
            print("gunicorn not installed, falling back to Flask dev server")
            app.run(host=host, port=port)
    else:
        app.run(host=host, port=port, debug=app.config['DEBUG'])

if __name__ == '__main__':
    main()