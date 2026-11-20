class RetrievalService:

    def __init__(self, qdrant_client, collection_name):

        self.client = qdrant_client
        self.collection_name = collection_name

    async def retrieve(self, embedding, top_k=5):

        result = await self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=top_k,
            with_payload=True
        )

        documents = []

        for point in result.points:

            payload = point.payload or {}

            documents.append({
                "text": (
                    payload.get("text")
                    or payload.get("page_content")
                    or payload.get("content")
                    or payload.get("summarized_data")
                    or ""
                ),
                "title": payload.get("title"),
                "source_url": payload.get("source_url"),
                "score": point.score
            })

        return [
            doc for doc in documents
            if doc["text"].strip()
        ]