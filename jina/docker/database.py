
import pymongo

from ..excepts import MongoDBException
from ..logging import get_logger


class MongoDBHandler:
    """
    Mongodb Handler to connect to the database & insert documents in the collection
    """
    def __init__(self, hostname: str, username: str, password: str,
                 database_name: str, collection_name: str):
        self.logger = get_logger(self.__class__.__name__)
        self.hostname = hostname
        self.username = username
        self.password = password
        self.database_name = database_name
        self.collection_name = collection_name
        self.connection_string = \
            f'mongodb+srv://{self.username}:{self.password}@{self.hostname}'
        
    def __enter__(self):
        return self.connect()
    
    def connect(self):
        try:
            self.client = pymongo.MongoClient(self.connection_string)
            self.client.admin.command('ismaster')
            self.logger.info('Successfully connected to the database')
        except pymongo.errors.ConnectionFailure:
            raise MongoDBException('Database server is not available')
        except pymongo.errors.ConfigurationError:
            raise MongoDBException('Credentials passed are not correct!')
        except pymongo.errors.PyMongoError as exp:
            raise MongoDBException(exp)
        return self
        
    @property
    def database(self):
        return self.client[self.database_name]
    
    @property
    def collection(self):
        return self.database[self.collection_name]
    
    def insert(self, document: str):
        result = self.collection.insert_one(document)
        self.logger.info(f'Pushed current summary to the database')
        return result.inserted_id
    
    def __exit__(self,  exc_type, exc_val, exc_tb):
        try:
            self.client.close()
        except pymongo.errors.PyMongoError as exp:
            raise MongoDBException(exp)
