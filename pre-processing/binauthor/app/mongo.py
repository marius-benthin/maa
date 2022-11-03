from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from app.config import Secrets


class MongoDB:

    def __init__(self):
        _config: Secrets = Secrets()
        self._client: MongoClient = MongoClient(_config.mongodb_uri)
        self._database: Database = self._get_database(_config.mongodb_database)
        self.collection_function_labels: Collection = self._get_collection("FunctionLabels")

    def _get_database(self, name: str) -> Database:
        """
        Get the database and create it if it not exists
        :param name: database name
        :return: database
        """
        if name not in self._client.list_database_names():
            return self._client[name]
        else:
            return self._client.get_database(name)

    def _get_collection(self, name: str) -> Collection:
        """
        Get the collection and create it if it not exists
        :param name: collection name
        :return: collection
        """
        if name not in self._database.list_collection_names():
            return self._database[name]
        else:
            return self._database.get_collection(name)
