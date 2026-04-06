from dotenv import load_dotenv
import os

load_dotenv()

HOST = os.getenv("MONGO_HOST", "localhost")
PORT = int(os.getenv("MONGO_PORT", "27017"))
USERNAME = os.getenv("MONGO_USERNAME", "root")
PASSWORD = os.getenv("MONGO_PASSWORD", "root")
DATABASE = os.getenv("MONGO_DATABASE", "tourisme_data")
TIMEOUT = int(os.getenv("MONGO_TIMEOUT", "5000"))

# Collections
COLLECTION_RAW = os.getenv("MONGO_COLLECTION_RAW", "place_raw")
COLLECTION_CLEAN = os.getenv("MONGO_COLLECTION_CLEAN", "place_clean")
