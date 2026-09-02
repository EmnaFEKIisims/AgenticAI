from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
print("Collections:", client.get_collections())
print("Qdrant OK ✅")