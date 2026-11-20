import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

url = os.getenv("QDRANT_URL")
api_key = os.getenv("QDRANT_API_KEY")

print("Qdrant URL configured:", bool(url))
print("API key configured:", bool(api_key))

client = QdrantClient(
    url=url,
    api_key=api_key,
    timeout=30
)

try:
    collections = client.get_collections()

    print("Successfully connected to Qdrant!")
    print("Available collections:")

    for collection in collections.collections:
        print("-", collection.name)

except Exception as e:
    print("Qdrant connection failed:")
    print(type(e).__name__, str(e))