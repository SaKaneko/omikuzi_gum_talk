import markdown as _md
import bleach

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "code",
    "pre",
    "a",
    "blockquote",
    "h1",
    "h2",
    "h3",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
}


class MarkdownRenderer:
    def __init__(self):
        pass

    def render(self, text: str) -> str:
        if text is None:
            return ""
        html = _md.markdown(text, extensions=["fenced_code", "codehilite"])
        clean = bleach.clean(
            html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
        )
        return clean
