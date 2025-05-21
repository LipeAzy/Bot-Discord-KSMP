from discord import app_commands

def setup_commands(tree: app_commands.CommandTree):
    @tree.command(name="ping", description="Responde com pong!")
    async def ping_slash(interaction):
        await interaction.response.send_message("Pong!", ephemeral=True)
