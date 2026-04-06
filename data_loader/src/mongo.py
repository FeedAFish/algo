from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
from .configs import *


class MongoConnection:
    def __init__(
        self,
    ):
        self.host = HOST
        self.port = PORT
        self.username = USERNAME
        self.password = PASSWORD
        self.database = DATABASE
        self.timeout = TIMEOUT
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
        self.connect()

    def connect(self) -> bool:
        try:
            connection_string = (
                f"mongodb://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/?authSource=admin"
            )

            self.client = MongoClient(
                connection_string, serverSelectionTimeoutMS=self.timeout
            )
            self.client.admin.command("ping")
            self.db = self.client[self.database]

            print(f"Connected to MongoDB at {self.host}:{self.port}")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    def disconnect(self) -> None:
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def change_collection(self, collection_name: str):
        if self.db is None:
            raise RuntimeError("Not connected to MongoDB")
        self.collection = self.db[collection_name]

    def change_raw_collection(self):
        self.change_collection(COLLECTION_RAW)

    def change_clean_collection(self):
        self.change_collection(COLLECTION_CLEAN)
