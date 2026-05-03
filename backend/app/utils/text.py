def build_embedding_text(ref: str, category: str, text_he: str, text_en: str) -> str:
    parts = [f'Ref: {ref}', f'Category: {category}']
    if text_he:
        parts.append(f'Hebrew: {text_he}')
    if text_en:
        parts.append(f'English: {text_en}')
    return '\n'.join(parts)
