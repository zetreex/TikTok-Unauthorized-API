import logging

from flask import Flask
from flask_cors import CORS
from flask_restplus import Api

from app.db.database import DataCleaner
from app.utils.device_pool import DevicePoll
from config.application import DEVICES_IN_POOL, USE_CACHING
from flask_executor import Executor


cors = CORS()
flask_api = Api()

def create_app():
    DevicePoll(DEVICES_IN_POOL)

    app = Flask(__name__)
    app.config['EXECUTOR_TYPE'] = 'thread'
    app.config['EXECUTOR_MAX_WORKERS'] = 50
    executor = Executor(app)

    # Init logger
    logging.basicConfig(level=logging.WARN)
    
    # Init api
    from app.api.base import ns as api_namespace, RestExecutorWrapper
    flask_api.init_app(app)
    flask_api.add_namespace(api_namespace)
    # Init plug-ins
    cors.init_app(app)
    RestExecutorWrapper(executor)

    from app.db.database import Database
    app.database = Database()
    app.database.create_tables()
    if USE_CACHING:
        DataCleaner().start()

    return app
