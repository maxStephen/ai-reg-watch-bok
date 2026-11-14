from regwatch.detect import canonical, fingerprint, unified_diff


def test_date_only_edits_do_not_change_fingerprint():
    a = "AI RMF Playbook\nLast updated: March 5, 2026\nSection 1 text"
    b = "AI RMF Playbook\nLast updated: September 24, 2026\nSection 1 text"
    assert fingerprint(a) == fingerprint(b)


def test_various_date_formats_are_masked():
    text = "2026-09-24 and 09/24/2026 and 24 Sep 2026 and Sept. 24, 2026 at 7:00 AM"
    assert "2026" not in canonical(text)
    assert "7:00" not in canonical(text)


def test_substantive_edit_changes_fingerprint():
    a = "Organizations should document AI risks."
    b = "Organizations must document AI risks."
    assert fingerprint(a) != fingerprint(b)


def test_unified_diff_shows_changed_lines():
    diff = unified_diff("line one\nline two", "line one\nline 2", "Src")
    assert "-line two" in diff and "+line 2" in diff
