from django.contrib import admin

from rag_api.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Configure the Django admin list and filters for indexed documents."""
    list_display = ('path', 'status', 'chunk_count', 'last_indexed_at')
    list_filter = ('status',)
    search_fields = ('path', 'sha256')
    readonly_fields = ('created_at', 'updated_at', 'last_indexed_at')
