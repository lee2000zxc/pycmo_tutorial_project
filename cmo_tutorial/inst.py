from __future__ import annotations

from html import unescape
from pathlib import Path
import re


_XML_DECL_RE = re.compile(r"<\?xml\b", re.IGNORECASE)
_COMMENT_RE = re.compile(
    r"<Comment>(.*?)</Comment>",
    re.IGNORECASE | re.DOTALL,
)


def extract_xml_from_inst_text(text: str) -> str:
    """Extract scenario XML from a CMO .inst file or accept raw XML."""
    stripped = text.lstrip()

    if stripped.startswith("<?xml") or stripped.startswith("<Scenario"):
        xml = stripped
    else:
        match = _COMMENT_RE.search(text)
        if match:
            xml = unescape(match.group(1))
        else:
            start = text.find("<?xml")
            if start < 0:
                start = text.find("<Scenario")
            if start < 0:
                raise ValueError(".inst 파일에서 Scenario XML을 찾지 못했습니다.")
            xml = text[start:]

    end = xml.rfind("</Scenario>")
    if end >= 0:
        xml = xml[: end + len("</Scenario>")]

    return repair_bare_ampersands(xml)


def repair_bare_ampersands(xml: str) -> str:
    """Escape only ampersands that are not already valid XML entities."""
    return re.sub(
        r"&(?!#\d+;|#x[0-9A-Fa-f]+;|amp;|lt;|gt;|quot;|apos;)",
        "&amp;",
        xml,
    )


def read_inst_xml(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp949", "utf-16"):
        try:
            return extract_xml_from_inst_text(raw.decode(encoding))
        except UnicodeDecodeError:
            continue
    return extract_xml_from_inst_text(raw.decode("utf-8", errors="replace"))
