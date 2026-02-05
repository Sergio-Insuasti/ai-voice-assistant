import re
def clean_response(text:str) -> str:
    # Remove bold / italics (**text**, *text*)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)

    # Remove inline code (`text`)
    text = re.sub(r'`(.*?)`', r'\1', text)

    # Remove headings (#)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

    return text.strip()