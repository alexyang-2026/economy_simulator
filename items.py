import json
import numpy as np

def load_items_and_recipes():
    with open("game/items.json", "r", encoding="utf-8") as items_file:
        gameitems = json.load(items_file)

    with open("game/recipes.json", "r", encoding="utf-8") as recipes_file:
        gamerecipes = json.load(recipes_file)

    return gameitems, gamerecipes


def verify_items_and_recipes(gamerecipes, gameitems):
    """
    Validate item references and quantities in crafting recipes.
    
    This function checks every input and output item in the the dictionary containing the game's items,
    and it also checks whether recipe quantities are positive integers.
    
    Args:
        gamerecipes (dict): Recipe definitions loaded from recipes.json.
        gameitems(dict): Item definitions loaded from items.json.
    
    Returns:
        bool: True if all references and quantities are valid
        False otherwise.

    Prints:
        Error messages identifying invalid items or noninteger, zero, or negative quantities.
    """

    no_absent_items = True
    no_invalid_quantities = True

    for recipe_id, recipe in gamerecipes.items():
        inputs = recipe["inputs"]
        outputs = recipe["outputs"]

        for item_id, quantity in inputs.items():
            if item_id not in gameitems:
                no_absent_items = False
                print(item_id, "is not in items.json")

            if type(quantity) != int or quantity <= 0:
                no_invalid_quantities = False
                print(item_id, "does not have a positive integer quantity of", quantity)

        for item_id, quantity in outputs.items():
            if item_id not in gameitems:
                no_absent_items = False
                print(item_id, "is not in items.json")
        
            if type(quantity) != int or quantity <= 0:
                no_invalid_quantities = False
                print(item_id, "does not have a positive integer quantity of", quantity)

    return no_absent_items and no_invalid_quantities


def build_crafting_matrices(gameitems, gamerecipes):
    """
    Construct input and output matrices for the crafting system.

    Each row represents an item, and each column represents a recipe.
    Matrix entries specify the quantities consumed or produced by
    executing a recipe once.

    Args:
        gameitems (dict): Item definitions loaded from items.json.
        gamerecipes (dict): Recipe definitions loaded from recipes.json.

    Returns:
        tuple: (C, B, item_index, recipe_index), where
            C (np.ndarray): Input quantities, shape (n_items, n_recipes).
            B (np.ndarray): Output quantities, shape (n_items, n_recipes).
            item_index (dict): Maps item IDs to matrix row indices.
            recipe_index (dict): Maps recipe IDs to matrix column indices.
    
    Matrix Definitions:
        C is a consumption (input) matrix that defines how many units of each item are consumed by each recipe.
        B is a production (output) matrix that defines how many units of each item are produced by each recipe.
    """

    recipe_index = {}

    # I called this j because it's the jth column in the recipe matrix
    for j, recipe_id in enumerate(gamerecipes):
        recipe_index[recipe_id] = j

    item_index = {}

    # i represents the ith row of the matrix
    for i, item_id in enumerate(gameitems):
        item_index[item_id] = i

    # Consumption matrix has shape ((length of gameitems), (length of recipes))
    C = np.zeros((len(gameitems), len(gamerecipes)), dtype=int)

    for recipe_id, recipe in gamerecipes.items():
        j = recipe_index[recipe_id]

        for item_id, quantity in recipe["inputs"].items():
            i = item_index[item_id]
            C[i, j] = quantity


    # Production matrix has same dimensions as C where 
    #   - The columns are the j different recipes
    #   - The rows are the i items that
    B = np.zeros((len(gameitems), len(gamerecipes)), dtype=int)

    for recipe_id, recipe in gamerecipes.items():
        j = recipe_index[recipe_id]

        for item_id, quantity in recipe["outputs"].items():
            i = item_index[item_id]
            B[i, j] = quantity


    return C, B, item_index, recipe_index







if __name__ == "__main__":
    gameitems, gamerecipes = load_items_and_recipes()

    if verify_items_and_recipes(gamerecipes, gameitems):
        print("No invalid items or invalid recipes :)")

    C, B, item_index, recipe_index = build_crafting_matrices(gameitems, gamerecipes)

    print("Consumption Matrix Shape:", C.shape)
    print("Produciton Matrix Shape:", B.shape)

    i = item_index["iron_ore"]
    j = recipe_index["smelt_iron"]

    print("Iron ore consumed:", C[i, j])

    i = item_index["iron_ingot"]

    print("Iron ingots produced:", B[i, j])

