from regwatch.config import load_sources


def test_shipped_sources_file_is_valid():
    sources = {s.id: s for s in load_sources()}
    iso = sources["iso-iec-42001"]
    assert iso.ai_allowed is False and iso.store_text is False
