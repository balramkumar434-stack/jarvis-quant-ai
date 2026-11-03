from risk import validate_order, RiskRejected

def test_valid_paper_order():
    result=validate_order("TEST","BUY",10,100,99)
    assert result["risk_amount"] == 10

def test_risk_limit_blocks():
    try:
        validate_order("TEST","BUY",100,100,90)
        assert False
    except RiskRejected:
        assert True
