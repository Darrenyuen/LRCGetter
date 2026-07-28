"""HTTP client for the QQ Music PC lyric endpoints."""

from __future__ import annotations

import binascii
from dataclasses import dataclass
from typing import Dict, Iterator
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup


SEARCH_URL = "https://c.y.qq.com/lyric/fcgi-bin/fcg_search_pc_lrc.fcg"
DOWNLOAD_URL = "https://c.y.qq.com/qqmusic/fcgi-bin/lyric_download.fcg"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 Chrome/126 Safari/537.36"
)


class QQMusicError(RuntimeError):
    """A network response or payload from QQ Music was invalid."""


@dataclass(frozen=True)
class Song:
    song_id: str
    title: str
    artist: str
    album: str


class QQMusicClient:
    def __init__(self, timeout: float = 20.0, session: requests.Session | None = None):
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {"User-Agent": USER_AGENT, "Referer": "https://y.qq.com/"}
        )

    def _get(self, url: str, **params: object) -> requests.Response:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise QQMusicError(f"QQ Music request failed: {exc}") from exc

    def search(self, title: str, artist: str = "", limit: int = 20) -> Iterator[Song]:
        response = self._get(
            SEARCH_URL,
            SONGNAME=title,
            SINGERNAME=artist,
            TYPE=2,
            RANGE_MIN=1,
            RANGE_MAX=max(1, min(limit, 50)),
        )
        soup = BeautifulSoup(response.content.decode("utf-8", errors="replace"), "xml")
        if soup.find("result") and soup.find("result").get_text(strip=True) != "0":
            reason = soup.find("reason")
            raise QQMusicError(
                f"QQ Music search rejected: {reason.get_text(strip=True) if reason else 'unknown'}"
            )
        for node in soup.find_all("songinfo"):
            yield Song(
                song_id=node.get("id", ""),
                title=self._decoded_text(node, "name"),
                artist=self._decoded_text(node, "singername"),
                album=self._decoded_text(node, "albumname"),
            )

    @staticmethod
    def _decoded_text(node: object, tag: str) -> str:
        child = node.find(tag)  # type: ignore[attr-defined]
        return unquote(child.get_text()) if child else ""

    def download(self, song_id: str) -> Dict[str, bytes]:
        response = self._get(
            DOWNLOAD_URL,
            version="15",
            miniversion="82",
            lrctype="4",
            musicid=song_id,
        )
        body = response.content.decode("utf-8", errors="replace")
        soup = BeautifulSoup(body.replace("<!--", "").replace("-->", ""), "xml")
        mapping = {"orig": "content", "ts": "contentts", "roma": "contentroma"}
        result: Dict[str, bytes] = {}
        for kind, tag in mapping.items():
            node = soup.find(tag)
            text = node.get_text(strip=True) if node else ""
            if not text:
                result[kind] = b""
                continue
            try:
                result[kind] = (
                    binascii.unhexlify(text)
                    if len(text) % 2 == 0
                    and all(char in "0123456789abcdefABCDEF" for char in text)
                    else text.encode("utf-8")
                )
            except (binascii.Error, ValueError) as exc:
                raise QQMusicError(f"Invalid {kind} lyric data") from exc
        if not any(result.values()):
            raise QQMusicError("QQ Music returned no lyric data for this song")
        return result
