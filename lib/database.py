import logging

from pymongo import MongoClient

log = logging.getLogger('database')


class Database:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance

    def __init__(self):
        self.db = None

        # Initialize database connection
        log.info('Connecting to the database...')
        client = MongoClient('mongodb://127.0.0.1:27017/apidata')
        self.db = client.get_database()

        log.info('Connected to the database, name: %s', self.db.name)
