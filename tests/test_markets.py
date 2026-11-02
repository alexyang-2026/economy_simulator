import numpy as np
import pytest
from markets import *

def test_transition_matrix():
    # Every column must sum to 1
    assert np.allclose(P.sum(axis=0), 1)
    
    # Probabilities must be between 0 and 1
    assert np.all((P >= 0) & (P <= 1))

def test_steady_state():
    pi = find_P_steady_state()
    
    assert np.isclose(np.sum(pi), 1)

    # Steady state has Pπ = π because eigenvalue is 1
    assert np.allclose(P @ pi, pi)

    assert np.all(pi >= 0)


def test_next_market_state():
    for current_state in range(len(STATES)):
        next_state = next_market_state(current_state)

        assert 0 <= next_state < len(STATES)


# MARKOV CHAIN TESTS
def test_price_is_positive():
    next_price = adjust_prices_from_markov_chain(
        current_state=2,
        current_price=25,
        equilibrium_price_vector=IRON_EQUILIBRIUM_PRICES
    )

    assert next_price > 0

def test_invalid_prices():
    with pytest.raises(ValueError):
        adjust_prices_from_markov_chain(
            2, 0, IRON_EQUILIBRIUM_PRICES
        )

    with pytest.raises(ValueError):
        adjust_prices_from_markov_chain(
            2, -10, IRON_EQUILIBRIUM_PRICES
        )


def test_mean_reversion(monkeypatch):
    monkeypatch.setattr("markets.random.gauss", lambda mu, sigma: 0)

    current_price = 25
    equilibrium_price = 18  # Rush state

    next_price = adjust_prices_from_markov_chain(
        3, current_price, IRON_EQUILIBRIUM_PRICES
    )

    expected_price = np.exp(
        np.log(current_price)
        + MEAN_REVERSION_RATE * (
            np.log(equilibrium_price) - np.log(current_price)
        )
    )

    assert np.isclose(next_price, expected_price)