"""Functions that validate user input"""


def is_valid_class(class_name: str, is_playable: bool) -> bool:
    """
    Checks that the class name and is_playable
    is valid before adding to the database."""
    if class_name is None or is_playable is None:
        return False
    if not isinstance(class_name, str):
        return False
    
    if not isinstance(is_playable, bool):
        return False
    
    if len(class_name) <= 2 or len(class_name) >  29:
        return False
    return True

if __name__ == "__main__":
    pass