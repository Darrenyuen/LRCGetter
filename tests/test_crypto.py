from lrcgetter.crypto import decrypt_blocks


def test_decrypt_block_matches_qqmusic_vector():
    encrypted = bytes.fromhex("1d54b68769414e57")
    assert decrypt_blocks(encrypted) == bytes.fromhex("789c4d985d8f56e5")
