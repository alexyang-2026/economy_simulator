import random
import time
import numpy as np

LAMBDA = 1 / 3

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


def process_market_updates(current_state, next_update):
    while time.monotonic() >= next_update:
        current_state = next_market_state(current_state)

        print(f"Market update! New state: {STATES[current_state]}")

        next_update += random.expovariate(LAMBDA)
        
    return current_state, next_update


IRON_EQUILIBRIUM_PRICES = np.array([45, 32, 25, 18, 12])

MEAN_REVERSION_RATE = 0.2
VOLATILITY_PARAMETER = 0.02

def adjust_prices_from_markov_chain(current_state, current_price, equilibrium_price_vector):
    """
    Purpose: Calculate the next commodity price using a Marov-switching log-price AR(1) model.

    Parameters:
        - current_state (int): the index of the current Markov economic state (an integer between 0-4).
        - current_price (float): a current commodity price P_t (see LaTeX documentation for full mathematical model).
        - equilibrium_price_vector (nparray): contains the equilibrium prices for each economic state.
    
    Returns the next commodity price P_{t+1}, which is strictly positive under valid inputs.

    For the full equation and mathematical model, it is best to reference LaTeX documentation.
    """
    equilibrium_price = equilibrium_price_vector[current_state] # because equilibrium_price_vetor is a 1D numpy vector

    # First check if the inputs are valid, because ln P_t only holds when P_t > 0 and similarly with the equilibrium price
    if current_price <= 0:
        raise ValueError("Current price must be strictly positive!")

    if equilibrium_price <= 0:
        raise ValueError("Equilibrium price must be strictly positive!")

    Z = random.gauss(0, 1)

    log_next_price = np.log(current_price) + (MEAN_REVERSION_RATE * (np.log(equilibrium_price) - np.log(current_price))) + VOLATILITY_PARAMETER * Z
    next_price = np.exp(log_next_price)
    
    return next_price
