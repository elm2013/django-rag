from django.apps import AppConfig


class RagApiConfig(AppConfig):
    """Configure the Django application that provides the RAG API."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rag_api'
