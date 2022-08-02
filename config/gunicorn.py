import os

host = os.getenv("APP_HOST", "0.0.0.0")
port = os.getenv("APP_PORT", "5001")

bind = f"{host}:{port}"

access_log_format = "%(h)s %(l)s %(u)s %(t)s '%(r)s' %(s)s %(b)s '%(f)s' '%(a)s' in %(D)sµs"  # noqa: E501

workers = int(os.getenv('WEB_CONCURRENCY', 4))
threads = int(os.getenv('PYTHON_MAX_THREADS', 16))