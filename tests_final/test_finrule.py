from dqpilot_final.finrule import explicit_balance, markdown_tables


def test_statement_heading_depth_and_empty_markdown_line_are_supported():
    text = '### Synthetic issuer — 2024\n\n| Item | Value |\n|---|---|\n\n| x | 2 |\n'
    result = markdown_tables(text)
    assert len(result) == 1 and result[0]['rows'] == [['Item', 'Value'], ['x', '2']]


def test_mezzanine_not_dropped_or_noncontrolling_double_counted():
    table = {'rows': [['Section', 'Subsection', 'Item', 'Value'],
        ['Assets', '', 'Total Assets', '110'], ['Liabilities', '', 'Total Liabilities', '80'],
        ['Equity', '', 'Total Equity', '25'], ['Mezzanine_Equity', '', 'Redeemable interests', '5']]}
    assert explicit_balance(table)['status'] == 'DISPLAY_EQUATION_SATISFIED'
    assert not explicit_balance(table)['semantic_validity_claim']
