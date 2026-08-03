import re
from html.parser import HTMLParser
from typing import Literal

_PRESENTATION_TAGS = {
	"a",
	"b",
	"blockquote",
	"br",
	"code",
	"div",
	"em",
	"h1",
	"h2",
	"h3",
	"h4",
	"h5",
	"h6",
	"hr",
	"i",
	"img",
	"li",
	"ol",
	"p",
	"pre",
	"span",
	"strong",
	"table",
	"tbody",
	"td",
	"th",
	"thead",
	"tr",
	"u",
	"ul",
}

_BOUNDARY_MARKERS = {
	"<<<TICKET_START>>>": "[[EMBEDDED_TICKET_START_MARKER]]",
	"<<<TICKET_END>>>": "[[EMBEDDED_TICKET_END_MARKER]]",
	"<<<DAI_LOG_START>>>": "[[EMBEDDED_DAI_LOG_START_MARKER]]",
	"<<<DAI_LOG_END>>>": "[[EMBEDDED_DAI_LOG_END_MARKER]]",
}


def _neutralize_boundaries(text: str) -> str:
	for marker, replacement in _BOUNDARY_MARKERS.items():
		text = text.replace(marker, replacement)
	return text


class _EvidenceExtractor(HTMLParser):
	def __init__(self) -> None:
		super().__init__(convert_charrefs=True)
		self.parts: list[str] = []
		self._endtag_start: int | None = None

	def handle_data(self, data: str) -> None:
		self.parts.append(data)

	def handle_comment(self, data: str) -> None:
		self.parts.append(data)

	def unknown_decl(self, data: str) -> None:
		if data.startswith("CDATA["):
			self.parts.append(data.removeprefix("CDATA["))

	def handle_starttag(
		self,
		tag: str,
		attrs: list[tuple[str, str | None]],
	) -> None:
		if tag not in _PRESENTATION_TAGS:
			self.parts.append(self.get_starttag_text())
		elif tag == "img":
			self.parts.append(next((value or "" for key, value in attrs if key == "alt"), ""))

	def handle_endtag(self, tag: str) -> None:
		if tag not in _PRESENTATION_TAGS:
			end = self.rawdata.find(">", self._endtag_start)
			self.parts.append(self.rawdata[self._endtag_start : end + 1])

	def handle_startendtag(
		self,
		tag: str,
		attrs: list[tuple[str, str | None]],
	) -> None:
		if tag not in _PRESENTATION_TAGS:
			self.parts.append(self.get_starttag_text())
		elif tag == "img":
			self.parts.append(next((value or "" for key, value in attrs if key == "alt"), ""))

	def parse_endtag(self, index: int) -> int:
		self._endtag_start = index
		try:
			return super().parse_endtag(index)
		finally:
			self._endtag_start = None


def frame_evidence_text(
	text: str,
	*,
	label: Literal["TICKET", "DAI_LOG"],
	max_chars: int = 100_000,
) -> str:
	if max_chars < 1:
		raise ValueError("max_chars must be positive")

	normalized = text.replace("\r\n", "\n").replace("\r", "\n")
	without_images = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", normalized)
	without_links = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", without_images)
	parser = _EvidenceExtractor()
	parser.feed(_neutralize_boundaries(without_links))
	parser.close()
	body = _neutralize_boundaries("".join(parser.parts))[:max_chars]
	return f"<<<{label}_START>>>\n{body}\n<<<{label}_END>>>"
