"""Functions that validate user input"""
import discord

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

def is_valid_settlement(ctx) -> tuple[bool, str]:
    """
    Checks if the command location is a valid settlement
    i.e. A thread inside of a forum
    """
    if not isinstance(ctx.channel, discord.Thread):
        return False, "This command must be used inside a forum thread."

    if not isinstance(ctx.channel.parent, discord.ForumChannel):
        return False, "This thread is not part of a forum channel."
    return True, None

if __name__ == "__main__":
    pass
