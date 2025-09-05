from typing import Dict


def render(template: str, args: Dict[str, str] = {}) -> str:
    """
    Render a template with placeholder values.
    Example: {{ title }} in template will be replaced with args["title"]
    """
    with open(template, "r") as f:
        content: str = f.read()

    for key, value in args.items():
        content = content.replace(f"{{{{ {key} }}}}", str(value))
    return content
