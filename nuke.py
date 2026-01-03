from qdrant_client import QdrantClient

QDRANT_URL = "http://localhost:6333"

client = QdrantClient(url=QDRANT_URL)

collections = client.get_collections().collections

print("\nCollections to be deleted:")
for c in collections:
    print(" -", c.name)

confirm = input("\nType NUKE to confirm: ")

if confirm != "NUKE":
    print("❎ Aborted.")
    exit(1)

for c in collections:
    print(f"❌ Deleting {c.name}")
    client.delete_collection(c.name)

print("\n💥 Done. Qdrant is empty.")
