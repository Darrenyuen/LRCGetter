"""Interactive command-line interface for LRCGetter."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, Sequence

from .client import QQMusicClient, QQMusicError, Song
from .converter import (
    extract_metadata,
    extract_qrc_text,
    safe_component,
    write_outputs,
)
from .crypto import QRCDecodeError, decrypt_qrc


def choose_song(songs: Sequence[Song]) -> Song | None:
    print("搜索结果保持 QQ 音乐接口返回顺序，本工具不做本地排序。")
    print(
        "提示：同名结果中较大的歌曲 ID 往往代表曲库条目较晚录入，"
        "歌词可能较新；这只是经验判断，请结合歌手和专辑选择。"
    )
    for index, song in enumerate(songs):
        print(
            f"#{index}: [ID {song.song_id}] {song.title} / "
            f"{song.artist or '未知歌手'} / {song.album or '未知专辑'}"
        )
    while True:
        selected = input("选择序号（直接回车取消）：#").strip()
        if not selected:
            return None
        try:
            index = int(selected)
            return songs[index] if index >= 0 else None
        except (ValueError, IndexError):
            print("序号无效，请重新输入。")


def decode_payloads(payloads: Dict[str, bytes]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for kind, payload in payloads.items():
        if not payload:
            result[kind] = ""
        elif payload.lstrip().startswith((b"[", b"<?xml")):
            result[kind] = extract_qrc_text(payload)
        else:
            result[kind] = extract_qrc_text(decrypt_qrc(payload))
    return result


def save_song_outputs(
    output_root: Path,
    song_id: str,
    title: str,
    artist: str,
    decoded: Dict[str, str],
) -> Path:
    destination = (
        output_root
        / f"{safe_component(title)}-{safe_component(artist)}"
        / f"{song_id}-{int(time.time())}"
    )
    created = write_outputs(destination, title, decoded)
    print(f"完成：{destination}")
    for path in created:
        print(f"  - {path.name}")
    return destination


def download_by_id(
    client: QQMusicClient,
    output_root: Path,
    song_id: str,
) -> bool:
    print(f"正在按 QQ 音乐歌曲 ID {song_id} 下载并转换歌词……")
    decoded = decode_payloads(client.download(song_id))
    metadata: Dict[str, str] = {}
    for kind in ("orig", "ts", "roma"):
        for key, value in extract_metadata(decoded.get(kind, "")).items():
            metadata.setdefault(key, value)
    title = metadata.get("ti") or f"QQMusic-{song_id}"
    artist = metadata.get("ar", "")
    save_song_outputs(output_root, song_id, title, artist, decoded)
    return True


def download_one(
    client: QQMusicClient,
    output_root: Path,
    title: str,
    artist: str = "",
) -> bool:
    print("正在搜索……")
    songs = list(client.search(title, artist))
    if not songs:
        print("没有搜索结果。")
        return False
    song = choose_song(songs)
    if song is None:
        return False
    print("正在下载并转换歌词……")
    destination = save_song_outputs(
        output_root,
        song.song_id,
        song.title,
        song.artist,
        decode_payloads(client.download(song.song_id)),
    )
    list_file = destination.parent / f"{safe_component(song.title)}-idlist.txt"
    list_file.write_text(
        "".join(
            f"#{i}: ({item.song_id}) {item.title} / {item.artist} / {item.album}\n"
            for i, item in enumerate(songs)
        ),
        encoding="utf-8",
    )
    return True


def song_id_argument(value: str) -> str:
    value = value.strip()
    if not value.isascii() or not value.isdecimal() or int(value) <= 0:
        raise argparse.ArgumentTypeError("歌曲 ID 必须是正整数")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="QQ 音乐逐字、逐行、翻译与罗马音歌词下载器（Windows / macOS 原生版）"
    )
    parser.add_argument("title", nargs="?", help="歌曲名；省略时进入交互模式")
    parser.add_argument("-a", "--artist", default="", help="歌手名")
    parser.add_argument(
        "--song-id",
        type=song_id_argument,
        help="跳过搜索，按 QQ 音乐歌曲 ID 直接下载",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "lyric",
        help="歌词输出目录",
    )
    parser.add_argument("--timeout", type=float, default=20.0, help="网络超时秒数")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.song_id and args.title:
        parser.error("歌曲名和 --song-id 不能同时使用")
    client = QQMusicClient(timeout=args.timeout)
    try:
        if args.song_id:
            return 0 if download_by_id(client, args.output, args.song_id) else 1
        if args.title:
            return 0 if download_one(
                client, args.output, args.title, args.artist
            ) else 1
        print("LRCGetter Windows / macOS 原生版（直接回车退出）")
        while True:
            query = input("\n歌曲名或 QQ 音乐歌曲 ID：").strip()
            if not query:
                return 0
            song_id = ""
            if query.lower().startswith("id:"):
                try:
                    song_id = song_id_argument(query.split(":", 1)[1])
                except argparse.ArgumentTypeError as exc:
                    print(f"输入无效：{exc}")
                    continue
            elif query.isascii() and query.isdecimal():
                confirmation = input(
                    f"检测到纯数字，按歌曲 ID {query} 直接下载？"
                    "（直接回车确认，输入 n 按歌名搜索）："
                ).strip().lower()
                if confirmation not in {"n", "no"}:
                    song_id = song_id_argument(query)
            if song_id:
                try:
                    download_by_id(client, args.output, song_id)
                except (QQMusicError, QRCDecodeError, ValueError) as exc:
                    print(f"失败：{exc}", file=sys.stderr)
                continue
            title = query
            artist = input("歌手名（可留空）：").strip()
            try:
                download_one(client, args.output, title, artist)
            except (QQMusicError, QRCDecodeError, ValueError) as exc:
                print(f"失败：{exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n已退出。")
        return 130
    except (QQMusicError, QRCDecodeError, ValueError) as exc:
        print(f"失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
