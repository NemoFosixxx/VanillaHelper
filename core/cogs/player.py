import disnake
import aiosqlite as sq
from disnake.ext import commands

class PlayerInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description='Получить информацию об игроке', name='player')
    async def player(self, inter: disnake.ApplicationCommandInteraction, user_id_or_nickname: str):
        async with sq.connect('whitelist.db') as db:
            async with db.execute('SELECT nickname, user_id FROM whitelist WHERE nickname = ? OR user_id = ?', (user_id_or_nickname, user_id_or_nickname)) as cursor:
                row = await cursor.fetchone()
                if row:
                    nickname, user_id = row
                    await inter.response.send_message(f'Nickname: {nickname}\nUser ID: {user_id}')
                else:
                    await inter.response.send_message('Игрок не найден в базе данных.')

def setup(bot: commands.Bot):
    bot.add_cog(PlayerInfo(bot))