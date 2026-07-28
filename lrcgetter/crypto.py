"""QQ Music QRC decryption for LRCGetter."""

from __future__ import annotations

import zlib

import pyqqmusicdes


QRC_KEY = b"!@#)(*$%123ZXC!@!@#)(NHL"


class QRCDecodeError(ValueError):
    """Raised when encrypted QRC data cannot be decoded."""


def decrypt_blocks(encrypted: bytes) -> bytes:
    """Run QQ Music's byte-compatible 3DES implementation."""
    if len(encrypted) % 8:
        raise QRCDecodeError(
            f"QRC payload length {len(encrypted)} is not a multiple of 8"
        )
    # The extension mirrors QQMusicCommon.dll and modifies the PyBytes buffer
    # in place, so always create a private copy first.
    result = bytes(bytearray(encrypted))
    status = pyqqmusicdes.decrypt_des(result, QRC_KEY)
    if status != 0:
        raise QRCDecodeError(f"QRC DES decoder returned status {status}")
    return result


def decrypt_qrc(encrypted: bytes) -> bytes:
    """Decrypt and decompress a QQ Music QRC payload.

    QQ Music uses 3-key Triple DES in ECB mode, followed by a zlib stream.
    The payload returned by its lyric endpoint is already block-aligned and
    has no PKCS padding.
    """
    if not encrypted:
        return b""
    try:
        compressed = decrypt_blocks(encrypted)
        return zlib.decompress(compressed, zlib.MAX_WBITS | 32)
    except (ValueError, zlib.error) as exc:
        raise QRCDecodeError("QRC decrypt/decompress failed") from exc
