"""Reserved extension point for an optional semantic embedding provider."""
class EmbeddingProvider:
    def embed(self, text: str): raise NotImplementedError("Configure an embedding provider to enable semantic search.")
