def split_text(text, chunk_size=1000, overlap=150):
    """Split text into overlapping, character-count-based chunks.

    Whitespace boundaries are preferred when they occur in the latter half
    of the candidate chunk. This is a simple character-based strategy; it
    does not enforce model-token limits or preserve Markdown structure.

    Args:
        text: Source text to split.
        chunk_size: Maximum target number of characters in each chunk.
        overlap: Number of characters carried over between adjacent chunks.

    Returns:
        list[str]: Non-empty chunks in their original order.

    Raises:
        ValueError: If ``chunk_size`` is not positive or overlap is outside
            the range from zero to ``chunk_size - 1``.
    """
    """Split text into overlapping character-based chunks.

    This simple splitter prefers whitespace boundaries. A later iteration can
    add Markdown heading/paragraph-aware splitting and token-based limits.
    """
    if chunk_size <= 0:
        raise ValueError('chunk_size must be greater than zero.')
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError('overlap must be between zero and chunk_size - 1.')

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            split_at = text.rfind(' ', start, end)
            if split_at > start + chunk_size // 2:
                end = split_at

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    return chunks
