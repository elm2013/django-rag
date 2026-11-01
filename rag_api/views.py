from django.shortcuts import render

# Create your views here.

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rag_api.services import answer_question


@csrf_exempt
@require_POST
def ask_question(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {'error': 'Invalid JSON body.'},
            status=400,
        )

    question = data.get('question', '')

    if not isinstance(question, str) or not question.strip():
        return JsonResponse(
            {'error': 'A question is required.'},
            status=400,
        )

    result = answer_question(question.strip())

    return JsonResponse(result)
    
    
