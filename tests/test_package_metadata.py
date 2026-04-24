import arc2_chimera


def test_version_string():
    assert isinstance(arc2_chimera.__version__, str)
    assert arc2_chimera.__version__.count(".") == 2


def test_disclaimer_is_honest():
    d = arc2_chimera.DISCLAIMER.lower()
    assert "not an arc prize submission" in d
    assert "proof-of-concept" in d


def test_status_shape():
    st = arc2_chimera.get_status()
    assert st["arc_prize_submission"] is False
    lo, hi = st["benchmark_accuracy_range"]
    assert 0.0 <= lo <= hi <= 0.1
