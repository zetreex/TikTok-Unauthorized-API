from app import create_app
from config.gunicorn import host, port

if __name__ == "__main__":
    app = create_app()
    app.run(host, port)