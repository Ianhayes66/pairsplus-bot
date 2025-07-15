import json
import trade_live

def test_positions_load_and_save(tmp_path):
    # Arrange
    test_file = tmp_path / "positions.json"
    trade_live.POSITIONS_FILE = test_file

    # Make sure positions is clean
    trade_live.positions = {}
    trade_live.save_positions()

    # Confirm empty file content
    with open(test_file) as f:
        data = json.load(f)
    assert data == {}

    # Add a position and save again
    trade_live.open_trade(("AAPL", "MSFT"), "LONG_SPREAD")
    with open(test_file) as f:
        data = json.load(f)
    assert "AAPL_MSFT" in data
    assert data["AAPL_MSFT"] == "LONG_SPREAD"

    # Reload positions
    trade_live.load_positions()
    assert trade_live.positions["AAPL_MSFT"] == "LONG_SPREAD"