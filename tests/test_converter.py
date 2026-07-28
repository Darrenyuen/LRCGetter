from pathlib import Path

import lrcgetter.cli
from lrcgetter.converter import (
    bilingual_lrc,
    char_lrc,
    extract_metadata,
    extract_qrc_text,
    format_time,
    line_lrc,
    parse_qrc,
    write_outputs,
)


QRC = (
    "[offset:0]\n"
    "[1000,1000]你(1000,500)好(1500,500)\n"
    "[2500,500]呀(2500,500)"
)


def test_parse_and_formats():
    ignored, lines = parse_qrc(QRC)
    assert ignored == ["[offset:0]"]
    assert line_lrc(lines) == "[00:01.00]你好\n[00:02.50]呀\n"
    assert char_lrc(lines) == (
        "[00:01.00]你[00:01.50]好[00:02.00]\n"
        "[00:02.50]呀[00:03.00]\n"
    )
    assert format_time(59999) == "01:00.00"


def test_xml_and_bilingual():
    xml = (
        '<?xml version="1.0"?><QrcInfos><LyricInfo>'
        '<Lyric_1 LyricType="1" LyricContent="[1000,500]A(1000,500)"/>'
        "</LyricInfo></QrcInfos>"
    )
    assert extract_qrc_text(xml.encode()) == "[1000,500]A(1000,500)"
    original = parse_qrc("[1000,500]A(1000,500)")[1]
    translated = parse_qrc("[1000,500]甲(1000,500)")[1]
    assert bilingual_lrc(original, translated) == (
        "[00:01.00]A[00:01.50]\n[00:01.48]甲\n"
    )


def test_extract_metadata():
    assert extract_metadata("[ti:歌名]\n[ar:歌手]\n[offset:0]") == {
        "ti": "歌名",
        "ar": "歌手",
        "offset": "0",
    }


def test_all_output_types(tmp_path: Path):
    created = write_outputs(
        tmp_path,
        "歌/名",
        {"orig": QRC, "ts": "[1000,1000]您好", "roma": QRC},
    )
    names = {path.name for path in created}
    assert "歌＿名-og-line.lrc" in names
    assert "歌＿名-og-char.lrc" in names
    assert "歌＿名-ch-line.lrc" in names
    assert "歌＿名-rm-line.lrc" in names
    assert "歌＿名-rm-char.lrc" in names
    assert "歌＿名-og&ch-mix.lrc" in names


def test_direct_mode_reports_no_result_as_failure(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(lrcgetter.cli, "QQMusicClient", lambda timeout: object())
    monkeypatch.setattr(lrcgetter.cli, "download_one", lambda *args: False)

    assert lrcgetter.cli.main(["missing", "--output", str(tmp_path)]) == 1


def test_default_output_uses_the_current_working_directory(
    monkeypatch, tmp_path: Path
):
    monkeypatch.chdir(tmp_path)

    assert lrcgetter.cli.build_parser().parse_args([]).output == tmp_path / "lyric"


def test_song_id_download_uses_embedded_metadata(tmp_path: Path):
    class Client:
        def download(self, song_id: str):
            assert song_id == "42"
            return {
                "orig": (
                    b"[ti:Song]\n[ar:Artist]\n"
                    b"[1000,500]A(1000,500)"
                ),
                "ts": b"",
                "roma": b"",
            }

    assert lrcgetter.cli.download_by_id(Client(), tmp_path, "42")
    output_root = tmp_path / "Song-Artist"
    generated = list(output_root.rglob("Song-og-line.lrc"))
    assert len(generated) == 1
    assert generated[0].read_text(encoding="utf-8") == "[00:01.00]A\n"


def test_interactive_numeric_query_can_download_by_id(monkeypatch, tmp_path: Path):
    inputs = iter(["42", "", ""])
    downloaded: list[str] = []
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    monkeypatch.setattr(lrcgetter.cli, "QQMusicClient", lambda timeout: object())
    monkeypatch.setattr(
        lrcgetter.cli,
        "download_by_id",
        lambda client, output, song_id: downloaded.append(song_id) or True,
    )

    assert lrcgetter.cli.main(["--output", str(tmp_path)]) == 0
    assert downloaded == ["42"]


def test_interactive_rejects_zero_song_id(monkeypatch, tmp_path: Path, capsys):
    inputs = iter(["0", "", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    monkeypatch.setattr(lrcgetter.cli, "QQMusicClient", lambda timeout: object())

    assert lrcgetter.cli.main(["--output", str(tmp_path)]) == 0
    assert "歌曲 ID 必须是正整数" in capsys.readouterr().out
