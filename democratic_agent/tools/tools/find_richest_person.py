def find_richest_person(data: dict) -> str:
    """
    Find the richest person in the given data.

    Args:
        data (dict): A dictionary where keys are person names and values are their wealth.

    Returns:
        str: The name of the richest person.
    """
    richest_person = max(data, key=data.get)
    return richest_person
