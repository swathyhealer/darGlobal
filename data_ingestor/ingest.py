
import os
import csv
import uuid
import hashlib
import logging

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv(
    "COLLECTION_NAME", "darglobal_knowledge"
)
CSV_FILE = os.getenv("CSV_FILE", "darglobal_data.csv")

MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

VECTOR_SIZE = 384
BATCH_SIZE = 64

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("Missing QDRANT_URL or QDRANT_API_KEY")


# --------------------------------------------------
# Initialize embedding model
# --------------------------------------------------

logger.info("Loading embedding model...")

embedding_model = SentenceTransformer(
    MODEL_NAME,
    device="cpu"
)

logger.info("Embedding model loaded successfully.")


# --------------------------------------------------
# Initialize Qdrant
# --------------------------------------------------

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=60
)



def create_collection():

    existing_collections = [
        collection.name
        for collection in client.get_collections().collections
    ]

    if COLLECTION_NAME in existing_collections:

        logger.warning(
            f"Collection '{COLLECTION_NAME}' already exists. "
            "Deleting existing data..."
        )

        client.delete_collection(
            collection_name=COLLECTION_NAME
        )

        logger.info("Existing collection deleted.")

    logger.info("Creating a fresh Qdrant collection...")

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE,
            distance=models.Distance.COSINE
        )
    )

    logger.info("Fresh collection created successfully.")



# --------------------------------------------------
# Generate deterministic point IDs
# --------------------------------------------------

def generate_point_id(title, source_url):

    unique_string = f"{source_url}|{title}"

    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            unique_string
        )
    )


# --------------------------------------------------
# Read CSV and prepare documents
# --------------------------------------------------

def load_documents():

    documents = []

    logger.info(f"Reading CSV: {CSV_FILE}")

    with open(
        CSV_FILE,
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "title",
            "summarized_data",
            "source_url",
            "additional_information"
        }

        actual_columns = set(reader.fieldnames or [])

        missing_columns = required_columns - actual_columns

        if missing_columns:
            raise ValueError(
                f"Missing CSV columns: {missing_columns}"
            )

        for row_number, row in enumerate(reader, start=2):

            title = (row.get("title") or "").strip()
            summarized_data = (
                row.get("summarized_data") or ""
            ).strip()

            source_url = (
                row.get("source_url") or ""
            ).strip()

            additional_information = (
                row.get("additional_information") or ""
            ).strip()

            # Skip rows with no actual content
            if not title and not summarized_data:
                logger.warning(
                    f"Skipping empty row: {row_number}"
                )
                continue

            # Combine title and summarized data
            combined_text = (
                f"Title: {title}\n\n"
                f"Content: {summarized_data}"
            )

            point_id = generate_point_id(
                title,
                source_url
            )

            documents.append({
                "id": point_id,
                "text": combined_text,
                "metadata": {
                    "title": title,
                    "source_url": source_url,
                    "additional_information": additional_information
                }
            })

    logger.info(
        f"Successfully loaded {len(documents)} documents."
    )

    return documents


# --------------------------------------------------
# Generate embeddings and upload to Qdrant
# --------------------------------------------------

def ingest_documents(documents):

    total_documents = len(documents)

    if total_documents == 0:
        logger.warning("No documents found.")
        return

    uploaded = 0

    for start in range(0, total_documents, BATCH_SIZE):

        batch = documents[
            start:start + BATCH_SIZE
        ]

        texts = [
            doc["text"] for doc in batch
        ]

        logger.info(
            f"Generating embeddings: "
            f"{start + 1}-{start + len(batch)} "
            f"of {total_documents}"
        )

        embeddings = embedding_model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        points = []

        for doc, embedding in zip(batch, embeddings):

            payload = {
                "text": doc["text"],
                **doc["metadata"]
            }

            points.append(
                models.PointStruct(
                    id=doc["id"],
                    vector=embedding.tolist(),
                    payload=payload
                )
            )

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True
        )

        uploaded += len(points)

        logger.info(
            f"Uploaded {uploaded}/{total_documents} documents."
        )

    logger.info("Ingestion completed successfully!")


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    create_collection()

    documents = load_documents()

    ingest_documents(documents)

    collection_info = client.get_collection(
        collection_name=COLLECTION_NAME
    )

    logger.info(
        f"Total vectors in Qdrant: "
        f"{collection_info.points_count}"
    )


if __name__ == "__main__":
    main()
