"""Public-domain-style deterministic EPUB fixture used by Book-to-Learning tests."""

from __future__ import annotations

import io
import zipfile


def minimal_structured_epub() -> bytes:
    """Build a legal, tiny EPUB3 with spine, nav, footnote, image and internal links."""
    files = {
        "META-INF/container.xml": b"""<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf"
    media-type="application/oebps-package+xml"/></rootfiles>
</container>""",
        "OEBPS/content.opf": b"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:askora:minimal-structured-book</dc:identifier>
    <dc:title>Askora Structured Learning</dc:title><dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="chapter-one" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="chapter-two" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
    <item id="figure" href="figure.svg" media-type="image/svg+xml"/>
  </manifest>
  <spine><itemref idref="chapter-one"/><itemref idref="chapter-two"/></spine>
</package>""",
        "OEBPS/nav.xhtml": b"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Contents</title></head><body><nav epub:type="toc"><ol>
<li><a href="chapter1.xhtml">Foundations</a></li>
<li><a href="chapter2.xhtml">Application</a></li>
</ol></nav></body></html>""",
        "OEBPS/chapter1.xhtml": b"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Foundations</title></head><body>
<h1 id="foundations">Foundations</h1>
<p id="definition">A stable source anchor preserves the origin of a learning fact.</p>
<p>Read the supporting <a href="#note-one">footnote</a>.</p>
<aside id="note-one" epub:type="footnote"><p>A footnote remains linked to its source.</p></aside>
<figure id="figure-one"><img src="figure.svg" alt="A source-to-evidence diagram"/></figure>
</body></html>""",
        "OEBPS/chapter2.xhtml": b"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Application</title></head><body>
<h1>Application</h1><h2>Replay</h2>
<p>Replay validates the locator and content hash before evidence publication.</p>
<ul><li>Use the exact spine order.</li><li>Fail closed when the anchor changes.</li></ul>
<p><a href="chapter1.xhtml#definition">Return to the source definition.</a></p>
</body></html>""",
        "OEBPS/figure.svg": b"""<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">
<rect width="10" height="10"/></svg>""",
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(
            zipfile.ZipInfo("mimetype", date_time=(2020, 1, 1, 0, 0, 0)),
            b"application/epub+zip",
            compress_type=zipfile.ZIP_STORED,
        )
        for name, content in files.items():
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED)
    return output.getvalue()
