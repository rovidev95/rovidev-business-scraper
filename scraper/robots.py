from __future__ import annotations

from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser


def robots_url_for(url: str) -> str:
    parts = urlparse(url)
    return urljoin(f"{parts.scheme}://{parts.netloc}", "/robots.txt")


def is_allowed(robots_txt: str | None, url: str, user_agent: str) -> bool:
    """Return whether ``url`` may be fetched under the given robots.txt body.

    A missing or empty robots.txt is treated as "allowed", which matches how
    well-behaved crawlers interpret a 404 on ``/robots.txt``.
    """
    if not robots_txt:
        return True
    parser = RobotFileParser()
    parser.parse(robots_txt.splitlines())
    return parser.can_fetch(user_agent, url)
