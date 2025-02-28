import discord


async def get_input(ctx, bot, prompt, convert_func=str, allow_zero=False):
    """Helper function to get user input with type conversion."""
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send(prompt)
    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        content = msg.content.strip()

        # Convert input if necessary
        if convert_func in (int, float):
            value = convert_func(content)
            if value == 0 and not allow_zero:
                await ctx.send("❌ Zero is not a valid option here. Try again.")
                return None
            return value
        return content
    except ValueError:
        await ctx.send("❌ Invalid input. Please enter a valid number.")
        return None
    except Exception:
        await ctx.send("❌ Timed out. Please try again.")
        return None


def create_embed(title, description, data_dict, color):
    """Creates an embed message for Discord with selectable options."""
    embed = discord.Embed(title=title, description=description, color=color)
    for name, _id in data_dict.items():
        embed.add_field(name=f"🔹 {name}", value=f"ID: `{_id}`", inline=False)
    return embed


if __name__ == "__main__":
    pass