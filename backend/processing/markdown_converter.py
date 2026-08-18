"""HTML to clean Markdown conversion module with MarkItDown adapter and fallback."""

import html
import io
import logging
import re

from backend.processing.exceptions import MarkdownConversionError


logger = logging.getLogger(__name__)

# Attempt importing Microsoft markitdown if present
try:
    from markitdown import MarkItDown

    _HAS_MARKITDOWN = True
except ImportError:
    _HAS_MARKITDOWN = False


class MarkdownConverter:
    """Converts sanitized HTML content into clean, semantic Markdown."""

    def __init__(self, use_markitdown: bool = True) -> None:
        """Initializes the MarkdownConverter.

        Args:
            use_markitdown: If True, attempts to use markitdown library if available.
        """
        self.use_markitdown = use_markitdown and _HAS_MARKITDOWN
        self._markitdown_instance: object | None = None
        if self.use_markitdown:
            try:
                self._markitdown_instance = MarkItDown()
                logger.info("MarkItDown engine enabled.")
            except Exception as e:
                logger.warning("Failed to initialize MarkItDown (%s). Using fallback parser.", e)
                self.use_markitdown = False
        else:
            logger.debug("Using internal semantic HTML-to-Markdown parser.")

    def convert(self, html_content: str) -> str:
        """Converts sanitized HTML markup into structured Markdown.

        Args:
            html_content: Sanitized HTML string.

        Returns:
            Structured Markdown string.

        Raises:
            MarkdownConversionError: If conversion fails completely.
        """
        if not html_content or not html_content.strip():
            return ""

        # Strategy 1: MarkItDown if enabled and available
        if self.use_markitdown and self._markitdown_instance is not None:
            try:
                # MarkItDown supports converting strings or stream-like content
                stream = io.BytesIO(html_content.encode("utf-8"))
                result = self._markitdown_instance.convert_stream(stream, file_extension=".html")
                if hasattr(result, "text_content") and result.text_content:
                    logger.debug("Successfully converted HTML via MarkItDown.")
                    return self._post_process_markdown(result.text_content)
            except Exception as e:
                logger.warning(
                    "MarkItDown conversion error (%s). Falling back to internal parser.",
                    str(e),
                )

        # Strategy 2: Internal robust semantic parser
        try:
            return self._semantic_html_to_markdown(html_content)
        except Exception as e:
            logger.error("Semantic Markdown conversion failed: %s", str(e), exc_info=True)
            raise MarkdownConversionError(f"HTML to Markdown conversion failed: {e}") from e

    def _semantic_html_to_markdown(self, html_str: str) -> str:
        """Internal HTML-to-Markdown parser preserving headings, lists, tables, and links.

        Args:
            html_str: HTML content to parse.

        Returns:
            Rendered Markdown text.
        """
        text = html_str

        # 1. Unescape basic entities first for consistency
        text = html.unescape(text)

        # 2. Convert Headings (h1 to h6)
        for level in range(1, 7):
            hashes = "#" * level
            heading_pattern = re.compile(
                rf"<h{level}\b[^>]*>(.*?)</h{level}>",
                re.IGNORECASE | re.DOTALL,
            )
            text = heading_pattern.sub(
                lambda m, h=hashes: f"\n\n{h} {self._strip_tags(m.group(1)).strip()}\n\n",
                text,
            )

        # 3. Convert Tables
        text = self._convert_tables(text)

        # 4. Convert Unordered Lists (ul) and Ordered Lists (ol)
        text = self._convert_lists(text)

        # 5. Convert Blockquotes
        blockquote_pattern = re.compile(
            r"<blockquote\b[^>]*>(.*?)</blockquote>", re.IGNORECASE | re.DOTALL
        )
        text = blockquote_pattern.sub(
            lambda m: f"\n\n> {self._strip_tags(m.group(1)).strip()}\n\n",
            text,
        )

        # 6. Convert Code blocks (<pre><code>) and inline (<code>)
        pre_code_pattern = re.compile(
            r"<pre\b[^>]*><code\b[^>]*>(.*?)</code></pre>|<pre\b[^>]*>(.*?)</pre>",
            re.IGNORECASE | re.DOTALL,
        )
        text = pre_code_pattern.sub(
            lambda m: f"\n\n```\n{self._strip_tags(m.group(1) or m.group(2)).strip()}\n```\n\n",
            text,
        )

        inline_code_pattern = re.compile(r"<code\b[^>]*>(.*?)</code>", re.IGNORECASE | re.DOTALL)
        text = inline_code_pattern.sub(
            lambda m: f"`{self._strip_tags(m.group(1)).strip()}`",
            text,
        )

        # 7. Convert Formatting: Bold, Italic, Strikethrough
        text = re.sub(
            r"<(?:strong|b)\b[^>]*>(.*?)</(?:strong|b)>",
            lambda m: f"**{self._strip_tags(m.group(1)).strip()}**",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        text = re.sub(
            r"<(?:em|i)\b[^>]*>(.*?)</(?:em|i)>",
            lambda m: f"*{self._strip_tags(m.group(1)).strip()}*",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # 8. Convert Links (<a href="...">text</a>)
        link_pattern = re.compile(
            r"<a\b[^>]*href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL
        )
        text = link_pattern.sub(
            lambda m: (
                f"[{self._strip_tags(m.group(2)).strip()}]({m.group(1).strip()})"
                if self._strip_tags(m.group(2)).strip()
                else ""
            ),
            text,
        )

        # 9. Convert Paragraphs and Line Breaks
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(
            r"<p\b[^>]*>(.*?)</p>",
            lambda m: f"\n\n{m.group(1).strip()}\n\n",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        text = re.sub(r"<hr\s*/?>", "\n\n---\n\n", text, flags=re.IGNORECASE)

        # 10. Strip remaining HTML tags
        text = self._strip_tags(text)

        return self._post_process_markdown(text)

    def _convert_tables(self, html_str: str) -> str:
        """Converts HTML tables to Markdown tables.

        Args:
            html_str: HTML content containing table markup.

        Returns:
            HTML text with tables converted to Markdown representation.
        """
        table_pattern = re.compile(r"<table\b[^>]*>(.*?)</table>", re.IGNORECASE | re.DOTALL)

        def replace_table(match: re.Match[str]) -> str:
            table_content = match.group(1)
            row_pattern = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
            cell_pattern = re.compile(
                r"<(?:th|td)\b[^>]*>(.*?)</(?:th|td)>", re.IGNORECASE | re.DOTALL
            )

            rows: list[list[str]] = []
            for row_match in row_pattern.finditer(table_content):
                cells = [
                    self._strip_tags(c.group(1)).replace("\n", " ").strip()
                    for c in cell_pattern.finditer(row_match.group(1))
                ]
                if any(cells):
                    rows.append(cells)

            if not rows:
                return ""

            # Standardize column count
            max_cols = max(len(r) for r in rows)
            padded_rows = [r + [""] * (max_cols - len(r)) for r in rows]

            # Generate markdown table
            header = padded_rows[0]
            separator = ["---"] * max_cols
            body = padded_rows[1:]

            md_lines: list[str] = [
                f"| {' | '.join(header)} |",
                f"| {' | '.join(separator)} |",
            ]
            for row in body:
                md_lines.append(f"| {' | '.join(row)} |")

            return "\n\n" + "\n".join(md_lines) + "\n\n"

        return table_pattern.sub(replace_table, html_str)

    def _convert_lists(self, html_str: str) -> str:
        """Converts unordered and ordered HTML lists to Markdown lists.

        Args:
            html_str: HTML content with list tags.

        Returns:
            Text with converted list formats.
        """
        # Process <ul>
        ul_pattern = re.compile(r"<ul\b[^>]*>(.*?)</ul>", re.IGNORECASE | re.DOTALL)

        def replace_ul(match: re.Match[str]) -> str:
            li_pattern = re.compile(r"<li\b[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL)
            items: list[str] = []
            for li in li_pattern.finditer(match.group(1)):
                item_text = self._strip_tags(li.group(1)).strip()
                if item_text:
                    items.append(f"* {item_text}")
            return "\n\n" + "\n".join(items) + "\n\n" if items else ""

        html_str = ul_pattern.sub(replace_ul, html_str)

        # Process <ol>
        ol_pattern = re.compile(r"<ol\b[^>]*>(.*?)</ol>", re.IGNORECASE | re.DOTALL)

        def replace_ol(match: re.Match[str]) -> str:
            li_pattern = re.compile(r"<li\b[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL)
            items: list[str] = []
            for idx, li in enumerate(li_pattern.finditer(match.group(1)), start=1):
                item_text = self._strip_tags(li.group(1)).strip()
                if item_text:
                    items.append(f"{idx}. {item_text}")
            return "\n\n" + "\n".join(items) + "\n\n" if items else ""

        return ol_pattern.sub(replace_ol, html_str)

    def _strip_tags(self, text: str) -> str:
        """Removes remaining HTML tags from text.

        Args:
            text: Text with possible HTML tags.

        Returns:
            Plain text without HTML tags.
        """
        return re.sub(r"<[^>]+>", " ", text)

    def _post_process_markdown(self, markdown_text: str) -> str:
        """Cleans and formats final Markdown output.

        Args:
            markdown_text: Raw converted Markdown.

        Returns:
            Normalized and compacted Markdown.
        """
        # Collapse multiple blank lines to max 2
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", markdown_text)
        # Collapse spaces within lines
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        return "\n".join(lines).strip()
