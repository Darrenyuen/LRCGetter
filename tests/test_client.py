from lrcgetter.client import DOWNLOAD_URL, SEARCH_URL, QQMusicClient, QQMusicError


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, responses: list[bytes]):
        self.headers: dict[str, str] = {}
        self.responses = iter(responses)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get(
        self, url: str, *, params: dict[str, object], timeout: float
    ) -> FakeResponse:
        self.calls.append((url, {"params": params, "timeout": timeout}))
        return FakeResponse(next(self.responses))


def test_search_preserves_upstream_query_and_decodes_metadata():
    session = FakeSession(
        [
            (
                b"<response><result>0</result><songlist>"
                b'<songinfo id="42">'
                b"<name>%E7%BA%A2%E8%8E%B2%E5%8D%8E</name>"
                b"<singername>LiSA</singername>"
                b"<albumname>%E7%BA%A2%E8%8E%B2%E5%8D%8E</albumname>"
                b"</songinfo></songlist></response>"
            )
        ]
    )
    client = QQMusicClient(timeout=3.5, session=session)

    songs = list(client.search("红莲华", "LiSA", limit=100))

    assert songs[0].song_id == "42"
    assert songs[0].title == "红莲华"
    assert songs[0].artist == "LiSA"
    url, request = session.calls[0]
    assert url == SEARCH_URL
    assert request["timeout"] == 3.5
    assert request["params"] == {
        "SONGNAME": "红莲华",
        "SINGERNAME": "LiSA",
        "TYPE": 2,
        "RANGE_MIN": 1,
        "RANGE_MAX": 50,
    }


def test_download_supports_encrypted_hex_and_plain_payloads():
    session = FakeSession(
        [
            (
                b"<!--<response>"
                b"<content>4142</content>"
                b"<contentts></contentts>"
                b"<contentroma>plain</contentroma>"
                b"</response>-->"
            )
        ]
    )
    client = QQMusicClient(session=session)

    assert client.download("42") == {
        "orig": b"AB",
        "ts": b"",
        "roma": b"plain",
    }
    url, request = session.calls[0]
    assert url == DOWNLOAD_URL
    assert request["params"]["musicid"] == "42"


def test_download_rejects_an_empty_lyric_response():
    session = FakeSession(
        [
            (
                b"<response><content></content><contentts></contentts>"
                b"<contentroma></contentroma></response>"
            )
        ]
    )

    try:
        QQMusicClient(session=session).download("42")
    except QQMusicError as exc:
        assert "no lyric data" in str(exc)
    else:
        raise AssertionError("empty lyric response should fail")
