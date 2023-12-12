def create_tool(name: str, description: str):
    """
    Creates a new tool, make it general to be usable with different arguments. i.e: search_on_google instead of search_for_specific_info
    Use this only in case no other function can satisfy the request.

    Args:
        name (str): The name of the tool, should match the expected function name. i.e: search_on_google
        description (str): A description used to create the tool, should include all the details.

    Returns:
        callable: The tool that was created.
    """
    return name, description


# Should we add here call_LLM?.
