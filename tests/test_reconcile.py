from lotbook.reconcile import reconcile


def row(qty="10", proceeds="100.00", basis="90.00", code="", adj="0.00", gain="10.00", term="SHORT", sold="2025-02-03"):
    return {
        "account": "A1",
        "symbol": "ABC",
        "quantity": qty,
        "date_acquired": "2025-01-02",
        "date_sold": sold,
        "proceeds": proceeds,
        "cost_basis": basis,
        "adjustment_code": code,
        "adjustment": adj,
        "gain_loss": gain,
        "term": term,
    }


def test_identical_rows_tie_out():
    result = reconcile([row()], [row()])
    assert result.ties_out and result.matched == 1


def test_one_cent_is_within_tolerance():
    assert reconcile([row(proceeds="100.01")], [row()]).ties_out


def test_money_difference_is_reported():
    result = reconcile([row(basis="95.00", gain="5.00")], [row()])
    assert not result.ties_out
    assert {diff.field for diff in result.differences} == {"cost_basis", "gain_loss"}


def test_code_and_term_compared():
    result = reconcile([row(term="LONG")], [row(code="W", term="short")])
    assert [diff.field for diff in result.differences] == ["adjustment_code", "term"]


def test_quantity_formats_are_equivalent():
    assert reconcile([row(qty="10")], [row(qty="10.000")]).ties_out


def test_unpaired_rows():
    result = reconcile([row(sold="2025-03-01")], [row()])
    assert len(result.only_ours) == 1 and len(result.only_broker) == 1
    assert not result.ties_out


def test_rows_with_same_key_pair_in_order():
    ours = [row(proceeds="100.00"), row(proceeds="200.00", gain="110.00")]
    broker = [row(proceeds="100.00"), row(proceeds="200.00", gain="110.00")]
    assert reconcile(ours, broker).ties_out
