"""Deterministic, structure-preserving EPUB parsing and source replay.

The records produced here are SYS01-internal working data.  Canonical identities
are assigned by ``revision_builder`` after a MaterialRevision is known.
"""

from __future__ import annotations

import hashlib
import io
import posixpath
import re
from collections.abc import Iterable
from typing import Any, Literal

from lxml import etree

EPUB_PARSER_VERSION = "epub-structure-v2"
EPUB_LOCATOR_VERSION = "epub-locator-v1"

_BLOCK_TAGS = {
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "li",
    "table",
    "figure",
    "img",
    "pre",
    "code",
    "aside",
}
_CONTAINER_BLOCK_TAGS = {"figure", "aside", "pre"}


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _local_name(element: etree._Element) -> str:
    return etree.QName(element).localname.casefold()


def _element_text(element: etree._Element) -> str:
    tag = _local_name(element)
    if tag == "img":
        return _normalized_text(
            element.get("alt") or element.get("title") or element.get("src") or "image"
        )
    parts = list(element.itertext())
    if tag == "figure":
        parts.extend(
            child.get("alt") or child.get("title") or child.get("src") or "image"
            for child in element.iter()
            if isinstance(child.tag, str) and _local_name(child) == "img"
        )
    return _normalized_text(" ".join(parts))


def _content_hash(text: str) -> str:
    return hashlib.sha256(_normalized_text(text).encode("utf-8")).hexdigest()


def _dom_path(element: etree._Element) -> str:
    parts: list[str] = []
    current: etree._Element | None = element
    while current is not None and isinstance(current.tag, str):
        name = _local_name(current)
        siblings = [
            sibling
            for sibling in current.itersiblings(preceding=True)
            if isinstance(sibling.tag, str) and _local_name(sibling) == name
        ]
        parts.append(f"{name}[{len(siblings) + 1}]")
        current = current.getparent()
    return "/" + "/".join(reversed(parts))


def _parse_xhtml(content: bytes) -> etree._Element:
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        recover=True,
        load_dtd=False,
        huge_tree=False,
        remove_comments=True,
    )
    return etree.fromstring(content, parser=parser)


def _body(root: etree._Element) -> etree._Element:
    for element in root.iter():
        if isinstance(element.tag, str) and _local_name(element) == "body":
            return element
    return root


def _is_nested_in_container(element: etree._Element) -> bool:
    parent = element.getparent()
    while parent is not None:
        if isinstance(parent.tag, str) and _local_name(parent) in _CONTAINER_BLOCK_TAGS:
            return True
        parent = parent.getparent()
    return False


def _node_type(element: etree._Element) -> tuple[str, int | None]:
    tag = _local_name(element)
    if tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
        level = int(tag[1])
        return ("CHAPTER" if level == 1 else "SECTION"), level
    epub_type = " ".join(
        value
        for key, value in element.attrib.items()
        if etree.QName(key).localname.casefold() in {"type", "role"}
    ).casefold()
    element_id = (element.get("id") or "").casefold()
    if "footnote" in epub_type or "endnote" in epub_type or "note" in element_id:
        return ("ENDNOTE" if "endnote" in epub_type else "FOOTNOTE"), None
    return {
        "p": ("PARAGRAPH", None),
        "li": ("LIST", None),
        "table": ("TABLE", None),
        "figure": ("FIGURE", None),
        "img": ("IMAGE", None),
        "pre": ("CODE", None),
        "code": ("CODE", None),
        "aside": ("OTHER", None),
    }.get(tag, ("OTHER", None))


def _canonical_text(text: str, heading_level: int | None) -> str:
    if heading_level is None:
        return text
    return f"{'#' * min(max(heading_level, 1), 6)} {text}"


def _internal_links(element: etree._Element) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for child in element.iter():
        if not isinstance(child.tag, str) or _local_name(child) != "a":
            continue
        href = child.get("href")
        if not href or re.match(r"^[a-z][a-z0-9+.-]*:", href, re.IGNORECASE):
            continue
        links.append({"href": href, "label": _element_text(child)})
    return links


def _flatten_toc(items: Iterable[Any], parents: tuple[str, ...] = ()) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for item in items:
        children: Iterable[Any] = ()
        entry = item
        if isinstance(item, tuple) and len(item) == 2:
            entry, children = item
        title = _normalized_text(str(getattr(entry, "title", "") or ""))
        path = (*parents, title) if title else parents
        href = getattr(entry, "href", None)
        if isinstance(href, str) and href:
            result[posixpath.normpath(href.split("#", 1)[0])] = list(path)
        result.update(_flatten_toc(children, path))
    return result


def _spine_items(book: Any) -> list[tuple[int, str | None, Any]]:
    items: list[tuple[int, str | None, Any]] = []
    for spine_index, entry in enumerate(book.spine):
        item_id = entry[0] if isinstance(entry, tuple) else entry
        item = book.get_item_with_id(item_id)
        if item is None or not str(item.get_name()).casefold().endswith(
            (".xhtml", ".html", ".htm")
        ):
            continue
        items.append((spine_index, item_id, item))
    return items


def parse_epub_structure(file_content: bytes) -> dict[str, Any]:
    """Return deterministic EPUB structure in spine order (D01-021/D01-041)."""
    from ebooklib import epub

    book = epub.read_epub(io.BytesIO(file_content), options={"ignore_ncx": False})
    toc_paths = _flatten_toc(book.toc)
    nodes: list[dict[str, Any]] = [
        {
            "local_id": "book",
            "parent_local_id": None,
            "node_type": "BOOK",
            "ordinal": 0,
            "heading": None,
            "text": None,
            "canonical_text": None,
            "source_locator": {
                "kind": "epub",
                "locator_version": EPUB_LOCATOR_VERSION,
                "source_path": None,
                "node_path": "/",
                "spine_index": None,
                "spine_item_id": None,
                "href": None,
                "nav_path": [],
                "dom_path": "/",
            },
            "content_hash": _content_hash(""),
            "metadata": {},
        }
    ]
    canonical_parts: list[str] = []
    malformed_resources = 0
    ordinal = 1

    for spine_index, item_id, item in _spine_items(book):
        href = posixpath.normpath(str(item.get_name()))
        nav_path = toc_paths.get(href, [])
        chapter_local_id = f"spine:{spine_index}:{href}"
        nodes.append(
            {
                "local_id": chapter_local_id,
                "parent_local_id": "book",
                "node_type": "CHAPTER",
                "ordinal": ordinal,
                "heading": nav_path[-1] if nav_path else None,
                "text": None,
                "canonical_text": None,
                "source_locator": {
                    "kind": "epub",
                    "locator_version": EPUB_LOCATOR_VERSION,
                    "source_path": href,
                    "node_path": "/html[1]/body[1]",
                    "spine_index": spine_index,
                    "spine_item_id": item_id,
                    "href": href,
                    "nav_path": nav_path,
                    "dom_path": "/html[1]/body[1]",
                },
                "content_hash": _content_hash(""),
                "metadata": {"linear": True},
            }
        )
        ordinal += 1
        try:
            root = _parse_xhtml(item.get_content())
        except (etree.XMLSyntaxError, ValueError):
            malformed_resources += 1
            continue

        heading_stack: list[tuple[int, str]] = []
        emitted = 0
        for element in _body(root).iter():
            if not isinstance(element.tag, str):
                continue
            tag = _local_name(element)
            if tag not in _BLOCK_TAGS or _is_nested_in_container(element):
                continue
            text = _element_text(element)
            if not text:
                continue
            node_type, heading_level = _node_type(element)
            dom_path = _dom_path(element)
            local_id = f"spine:{spine_index}:{href}:{dom_path}"
            if heading_level is not None:
                while heading_stack and heading_stack[-1][0] >= heading_level:
                    heading_stack.pop()
                parent_local_id = heading_stack[-1][1] if heading_stack else chapter_local_id
                heading_stack.append((heading_level, local_id))
            else:
                parent_local_id = heading_stack[-1][1] if heading_stack else chapter_local_id
            canonical_text = _canonical_text(text, heading_level)
            nodes.append(
                {
                    "local_id": local_id,
                    "parent_local_id": parent_local_id,
                    "node_type": node_type,
                    "ordinal": ordinal,
                    "heading": text if heading_level is not None else None,
                    "text": text,
                    "canonical_text": canonical_text,
                    "source_locator": {
                        "kind": "epub",
                        "locator_version": EPUB_LOCATOR_VERSION,
                        "source_path": href,
                        "node_path": dom_path,
                        "spine_index": spine_index,
                        "spine_item_id": item_id,
                        "href": href,
                        "nav_path": nav_path,
                        "dom_path": dom_path,
                    },
                    "content_hash": _content_hash(text),
                    "metadata": {
                        "element_id": element.get("id"),
                        "internal_links": _internal_links(element),
                        "image_src": element.get("src") if tag == "img" else None,
                    },
                }
            )
            canonical_parts.append(canonical_text)
            ordinal += 1
            emitted += 1

        if emitted == 0:
            fallback_text = _element_text(_body(root))
            if fallback_text:
                dom_path = _dom_path(_body(root))
                nodes.append(
                    {
                        "local_id": f"spine:{spine_index}:{href}:{dom_path}:fallback",
                        "parent_local_id": chapter_local_id,
                        "node_type": "PARAGRAPH",
                        "ordinal": ordinal,
                        "heading": None,
                        "text": fallback_text,
                        "canonical_text": fallback_text,
                        "source_locator": {
                            "kind": "epub",
                            "locator_version": EPUB_LOCATOR_VERSION,
                            "source_path": href,
                            "node_path": dom_path,
                            "spine_index": spine_index,
                            "spine_item_id": item_id,
                            "href": href,
                            "nav_path": nav_path,
                            "dom_path": dom_path,
                        },
                        "content_hash": _content_hash(fallback_text),
                        "metadata": {"fallback": True},
                    }
                )
                canonical_parts.append(fallback_text)
                ordinal += 1

    full_text = "\n\n".join(canonical_parts)
    return {
        "format": "epub",
        "parser_version": EPUB_PARSER_VERSION,
        "root_local_id": "book",
        "nodes": nodes,
        "full_text": full_text,
        "chunks": canonical_parts,
        "metadata": {
            "format": "epub",
            "parser_version": EPUB_PARSER_VERSION,
            "total_chapters": len(_spine_items(book)),
            "node_count": len(nodes),
            "malformed_resource_count": malformed_resources,
            "spine_hrefs": [str(item.get_name()) for _, _, item in _spine_items(book)],
            "nav_paths": toc_paths,
        },
    }


def _matching_elements(content: bytes) -> list[tuple[str, str]]:
    root = _parse_xhtml(content)
    result: list[tuple[str, str]] = []
    for element in _body(root).iter():
        if not isinstance(element.tag, str):
            continue
        if _local_name(element) not in _BLOCK_TAGS or _is_nested_in_container(element):
            continue
        text = _element_text(element)
        if text:
            result.append((_dom_path(element), _content_hash(text)))
    return result


def replay_epub_locator(
    file_content: bytes,
    *,
    locator: dict[str, Any],
    expected_content_hash: str,
) -> tuple[Literal["EXACT", "RECOVERED", "FAILED"], str | None]:
    """Validate a persisted EPUB locator without guessing across resources (D01-051)."""
    from ebooklib import epub

    href = locator.get("href")
    dom_path = locator.get("dom_path")
    if not isinstance(href, str) or not href or not isinstance(dom_path, str):
        return "FAILED", None
    try:
        book = epub.read_epub(io.BytesIO(file_content), options={"ignore_ncx": False})
        item = book.get_item_with_href(href)
        if item is None:
            return "FAILED", None
        candidates = _matching_elements(item.get_content())
    except (etree.XMLSyntaxError, ValueError, OSError):
        return "FAILED", None
    for candidate_path, candidate_hash in candidates:
        if candidate_path == dom_path and candidate_hash == expected_content_hash:
            return "EXACT", candidate_path
    recovered = [path for path, value in candidates if value == expected_content_hash]
    if len(recovered) == 1:
        return "RECOVERED", recovered[0]
    return "FAILED", None
