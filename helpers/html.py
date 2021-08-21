def clean_text(text: str):
    delete = False
    clean = ''

    for char in text:
        if char == '>':
            delete = False
            continue
        elif delete:
            continue
        elif char == '<':
            delete = True
            continue
        else:
            clean += char

    # Replace line breaks tags
    clean.replace('<br/>', '\n')
    clean.replace('<br>', '\n')

    return clean
