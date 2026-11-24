"""WSGI entry point that runs migrations before serving requests."""

import app as service_app

service_app.retry_migrations()
app = service_app.app
