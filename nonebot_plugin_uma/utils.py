import re


def md_escape(text: str) -> str:
    pattern = r"([\\_*\[\](){}#+\-.!])"
    return re.sub(pattern, r"\\\1", text)
