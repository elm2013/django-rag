from django.urls import path

from rag_api.api.views import ask_question

urlpatterns = [
    path('ask/', ask_question, name='ask_question'),
]
