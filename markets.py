import random
import time
import numpy as np

LAMBDA = 1 / 60

STATES = [
    "severe_shortage",
    "shortage",
    "normal",
    "rush",
    "severe_rush"
]

# P is a Markov matrix
P = np.array([
    [0.70, 0.10, 0.01, 0.00, 0.00],
    [0.25, 0.70, 0.09, 0.02, 0.00],
    [0.05, 0.18, 0.80, 0.18, 0.05],
    [0.00, 0.02, 0.09, 0.70, 0.25],
    [0.00, 0.00, 0.01, 0.10, 0.70]
])

def find_P_steady_state():
    """
    Since P is a column-stochastic Markov Matrix, the steady state is the eigenvector associated with the eigenvalue 1.
    The steady state is a probability distribution whose component represents the long-run probability of the market occupying that economic state.
    
    This function finds that steady-state probability distribution of P.
    """
    P_eigenvalues, P_eigenvectors = np.linalg.eig(P)

    # Return the index of the eigenvalue closest to 1 (in case we have an eigenvalue like 0.999999998)
    # This is accomplished by subtracting 1 from every eigenvalue and getting its absolute value
    # This gets the distance of each eigenvalue from 1
    # The index of the smallest distance is what we want
    index = np.argmin(np.abs(P_eigenvalues - 1))

    if not np.isclose(P_eigenvalues[index], 1):
        raise ValueError("No eigenvalue sufficiently close to 1.")

    # P_eigenvectors is a numpy array but the COLUMNS are the eigenvectors
    # So [:, index] selects all rows first, then only the column whose index matches that of the eigenvalue
    steady_state_eigenvector = P_eigenvectors[:, index]

    # Normalize the eigenvector because we need it to be a probability distribution
    # The calculated eigenvector above may or may not be probabilities
    steady_state_eigenvector = steady_state_eigenvector / np.sum(steady_state_eigenvector)

    # The first time I ran this function to get the steady state it gave me a complex-valued eigenvector even though all the complex components were 0
    # This is to ensure it only returns real numbers if all complex components are sufficiently close to 0
    return np.real_if_close(steady_state_eigenvector)



def next_market_state(current_state):
    """
    Generate a new market state given the current market state.
    """
    probabilities = P[:, current_state]
    next_state = np.random.choice(len(STATES), p=probabilities)

    return next_state




# Used once to establish the first update deadlin
def schedule_next_market_update():
    # Generate the number of seconds until the next market update is due
    waiting_time = random.expovariate(LAMBDA)

    next_update = time.monotonic() + waiting_time
    return next_update


def process_market_updates(next_update):
    while time.monotonic() >= next_update:
        print("Market update!")
        next_update += random.expovariate(LAMBDA)
        
    return next_update

