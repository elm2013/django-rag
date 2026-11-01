from django.urls import path

from rag_api.websocket.consumers import RagConsumer

websocket_urlpatterns = [
    path('ws/rag/chat/', RagConsumer.as_asgi(), name='rag_chat'),
]
