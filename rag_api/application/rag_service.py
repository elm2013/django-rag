from django.conf import settings

from rag_api.llm.client import generate_answer
from rag_api.retrieval.retriever import retrieve_documents


def answer_question(question):
    """Retrieve relevant context and generate an answer for a question.

    Args:
        question: Non-empty natural-language question to answer.

    Returns:
        dict: Generated answer and the sources used to build its context.
    """
    retrieved = retrieve_documents(question, top_k=settings.RAG_TOP_K)

    if not retrieved:
        return {
            'answer': (
                'The indexed documents do not contain enough information.'
            ),
            'sources': [],
        }

    context_parts = []
    sources = []
    for index, item in enumerate(retrieved, start=1):
        context_parts.append(
            '[{}] Source: {}\n{}'.format(
                index,
                item['source'],
                item['text'],
            )
        )
        sources.append({
            'id': index,
            'source': item['source'],
            'distance': item['distance'],
        })

    answer = generate_answer(question, '\n\n'.join(context_parts))
    return {'answer': answer, 'sources': sources}
