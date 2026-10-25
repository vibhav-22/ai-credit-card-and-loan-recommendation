"""
HTML parser using BeautifulSoup:
Strips clutter, normalizes visible text, extracts headings,
and parses HTML tables into structured format for extraction.
"""
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup


class PageParser:
    def parse_html(self, html_content: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove clutter tags
        for tag in soup(["script", "style", "nav", "footer", "iframe", "svg", "noscript"]):
            tag.decompose()

        # Extract title
        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        # Extract headings
        headings: List[Dict[str, str]] = []
        for h in soup.find_all(["h1", "h2", "h3", "h4"]):
            text = h.get_text(separator=" ", strip=True)
            if text:
                headings.append({"level": h.name, "text": text})

        # Extract tables
        tables = self._extract_tables(soup)

        # Extract clean visible text
        body_text = soup.get_text(separator="\n", strip=True)
        # Normalize excessive newlines
        body_text = re.sub(r'\n{3,}', '\n\n', body_text)

        return {
            "title": title,
            "headings": headings,
            "tables": tables,
            "clean_text": body_text
        }

    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        extracted_tables = []
        for table in soup.find_all("table"):
            headers = []
            rows = []
            
            # Find headers in thead or first tr with th
            th_tags = table.find_all("th")
            if th_tags:
                headers = [th.get_text(strip=True) for th in th_tags]

            # Find rows
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells and cells != headers:
                    rows.append(cells)

            if rows or headers:
                extracted_tables.append({
                    "headers": headers,
                    "rows": rows
                })
        return extracted_tables
