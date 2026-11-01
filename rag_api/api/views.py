import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from rag_api.application.rag_service import answer_question


@require_POST
def ask_question(request):
    """Validate a question request and return its RAG-generated answer.

    Args:
        request: Django HTTP request containing a JSON ``question`` field.

    Returns:
        JsonResponse: The answer and source list, or a client/service error.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    question = data.get('question')
    if not isinstance(question, str) or not question.strip():
        return JsonResponse(
            {'error': 'A non-empty question is required.'},
            status=400,
        )

    try:
        result = answer_question(question.strip())
    except (ValueError, RuntimeError) as exc:
        return JsonResponse({'error': str(exc)}, status=503)

    return JsonResponse(result)
