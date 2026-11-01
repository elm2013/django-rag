from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.test import SimpleTestCase

from config.asgi import application


class RagConsumerTests(SimpleTestCase):
    """Tests for the RAG WebSocket protocol."""

    def test__ask_message__returns_answer_and_sources(self):
        """Return the RAG service result in the WebSocket answer format."""
        with patch(
            'rag_api.websocket.consumers.answer_question',
            return_value={
                'answer': 'A grounded answer.',
                'sources': [{'id': 1, 'source': 'guide.md', 'distance': 0.1}],
            },
        ) as answer_question:
            response = async_to_sync(self._send_message)({
                'type': 'ask',
                'question': '  What is RAG?  ',
            })

        answer_question.assert_called_once_with('What is RAG?')
        self.assertEqual(response['type'], 'answer')
        self.assertEqual(response['answer'], 'A grounded answer.')
        self.assertEqual(len(response['sources']), 1)

    def test__invalid_question__returns_error(self):
        """Reject an empty question without calling the RAG service."""
        with patch(
            'rag_api.websocket.consumers.answer_question'
        ) as answer_question:
            response = async_to_sync(self._send_message)({
                'type': 'ask',
                'question': '   ',
            })

        answer_question.assert_not_called()
        self.assertEqual(response['type'], 'error')
        self.assertEqual(
            response['error'],
            'A non-empty question is required.',
        )

    async def _send_message(self, message):
        """Connect, send one message, receive its response, and disconnect."""
        communicator = WebsocketCommunicator(
            application,
            '/ws/rag/chat/',
            headers=[
                (b'host', b'localhost'),
                (b'origin', b'http://localhost'),
            ],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to(message)
        response = await communicator.receive_json_from()
        await communicator.disconnect()
        return response
