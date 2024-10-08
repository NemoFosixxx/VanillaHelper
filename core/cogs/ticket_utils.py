import disnake
from disnake.ext import commands
import yaml


file_path = 'config.yml'
with open(file_path, 'r') as file:
    config = yaml.safe_load(file)

class TicketUtils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.allowed_categories = [1284369542398607391, 1288396219961573468, 1292151984761213060, 1292152137937063959, 1292152320443940886, 1292152345248923754] #id категорий, в которых можно юзать /add /remove

    @commands.slash_command(description='Добавить игрока в тикет', name='add')
    @commands.has_role(config.get('whitelist_role_id'))
    async def add_in_ticket(self, inter: disnake.ApplicationCommandInteraction, user_id: str):
        if inter.channel.category_id in self.allowed_categories:
            try:
                user_id = int(user_id)
            except ValueError:
                await inter.send("Некорректный Discord ID!", ephemeral=True)
                return
            
            
            user = inter.guild.get_member(user_id)
            if user is None:
                await inter.send("Пользователь с таким Discord ID не найден!", ephemeral=True)
                return
            else:
                overwrites = disnake.PermissionOverwrite(
                read_messages=True, send_messages=True, add_reactions=True, 
                embed_links=True, attach_files=True, read_message_history=True,
                external_emojis=True
                )
                await inter.channel.set_permissions(user, overwrite=overwrites)

                await inter.send(f"Пользователь <@{user_id}> был добавлен в этот тикет!")

        else:
            await inter.send("Эту команду можно использовать только в определённых категориях!", ephemeral=True)
            
    @commands.slash_command(description='Удалить игрока из тикета', name='remove')
    @commands.has_role(config.get('whitelist_role_id'))
    async def remove_from_ticket(self, inter: disnake.ApplicationCommandInteraction, user_id: str):
        if inter.channel.category_id in self.allowed_categories:
            try:
                user_id = int(user_id)
            except ValueError:
                await inter.send("Некорректный Discord ID!", ephemeral=True)
                
            user = inter.guild.get_member(user_id)
            if user is None:
                await inter.send("Пользователь с таким Discord ID не найден!", ephemeral=True)
                return
            else:
                overwrites = disnake.PermissionOverwrite(
                read_messages=False, send_messages=False, add_reactions=False, 
                embed_links=False, attach_files=False, read_message_history=False,
                external_emojis=False
                )
                await inter.channel.set_permissions(user, overwrite=overwrites)

                await inter.send(f"Пользователь <@{user_id}> был удалён из этого тикета!")
        else:
            await inter.send("Эту команду можно использовать только в определённых категориях!", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(TicketUtils(bot))
