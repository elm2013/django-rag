from channels.generic.websocket import JsonWebsocketConsumer

from rag_api.application.rag_service import answer_question


class RagConsumer(JsonWebsocketConsumer):
    """Handle interactive RAG questions over a WebSocket connection.

    The client sends JSON messages with the following structure::

        {"type": "ask", "question": "Your question"}

    Successful responses use the ``answer`` type and include the generated
    answer and its source documents. Invalid requests and service errors use
    the ``error`` type.

    The consumer is synchronous because the current RAG service, embedding
    model, ChromaDB client, and LLM client all expose synchronous interfaces.
    Channels runs synchronous consumers outside the ASGI event loop.
    """

    def connect(self):
        """Accept a new WebSocket connection."""
        self.accept()

    def receive_json(self, content, **kwargs):
        """Validate a client message and return its RAG answer.

        Args:
            content: Decoded JSON value received from the WebSocket client.
            **kwargs: Additional keyword arguments provided by Channels.

        Sends:
            A JSON ``answer`` message on success, or an ``error`` message
            when the message is invalid or answer generation fails.
        """
        if not isinstance(content, dict):
            self._send_error('A JSON object is required.')
            return

        if content.get('type') != 'ask':
            self._send_error('Unsupported message type.')
            return

        question = content.get('question')
        if not isinstance(question, str) or not question.strip():
            self._send_error('A non-empty question is required.')
            return

        try:
            result = answer_question(question.strip())
        except (ValueError, RuntimeError) as exc:
            self._send_error(str(exc))
            return

        self.send_json({
            'type': 'answer',
            'answer': result['answer'],
            'sources': result['sources'],
        })

    def _send_error(self, message):
        """Send a consistently structured error message to the client.

        Args:
            message: Human-readable explanation of the request or service
                error.
        """
        self.send_json({
            'type': 'error',
            'error': message,
        })
