def recursive_schema_merge(current_schema, update_patch):
    """
    Traverses deeply nested JSON matrices to mutate individual data coordinates 
    without overwriting or drop-killing parallel structural nodes.
    """
    for key, val in update_patch.items():
        if isinstance(val, dict) and key in current_schema and isinstance(current_schema[key], dict):
            recursive_schema_merge(current_schema[key], val)
        else:
            current_schema[key] = val
    return current_schema