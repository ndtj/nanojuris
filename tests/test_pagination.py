from __future__ import annotations

import pytest

from nanojuris.pagination import page_completeness


@pytest.mark.parametrize(
    ("total", "start", "returned", "authoritative", "expected"),
    [
        (0, 0, 0, True, True),
        (2, 1, 2, True, True),
        (10, 1, 2, True, False),
        (10, 9, 2, True, True),
        (10, 0, 0, True, False),
        (2, 1, 2, False, None),
        (None, 1, 2, True, None),
    ],
)
def test_page_completeness_is_conservative(
    total: int | None,
    start: int,
    returned: int,
    authoritative: bool,
    expected: bool | None,
) -> None:
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=returned,
        total_is_authoritative=authoritative,
    )

    assert complete is expected
    assert reason
