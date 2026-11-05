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
