import disnake
import aiosqlite as sq
from disnake.ext import commands
import yaml
import logging
from database.wh_database import db_start, add_to_db, remove_from_db
from mcrcon import MCRcon

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


file_path = 'config.yml'
with open(file_path, 'r') as file:
    config = yaml.safe_load(file)

class WhitelistAdder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.start_db())
        

    async def start_db(self):
        try:
            await db_start()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            
    def _send_rcon_command_sync(self, command):
        try:
            rcon_host = config.get('rcon_host')
            rcon_password = config.get('rcon_password')
            rcon_port = config.get('rcon_port')
            
            with MCRcon(rcon_host, rcon_password, rcon_port) as mcr:
                response = mcr.command(command)
                return response
        except Exception as e:
            return str(e)


    @commands.slash_command(description='Управление вайтлистом', name='whitelist')
    @commands.has_role(config.get('whitelist_role_id'))
    async def whitelist(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @whitelist.sub_command(description='Добавляет игрока в вайтлист', name='add')
    @commands.has_role(config.get('whitelist_role_id'))
    async def whitelist_add(self, inter: disnake.ApplicationCommandInteraction, nickname: str, user_id: str):
        await inter.response.defer()
        cmd_channel = self.bot.get_channel(config.get('alert_channel'))
        user = inter.user.name
        try:
            async with sq.connect('whitelist.db') as db:
                async with db.execute('SELECT nickname FROM whitelist WHERE user_id = ?', (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        await inter.edit_original_response(content=f'Пользователь с Discord ID {user_id} уже привязан к нику {row[0]}.')
                        return

            response = self._send_rcon_command_sync(f'whitelist add {nickname}')

            
            if 'Added' in response:
                await add_to_db(nickname, user_id)
                member = inter.guild.get_member(int(user_id))
                player_role = inter.guild.get_role(config.get('role_id'))
                if member and player_role:
                    await member.add_roles(player_role)
                    embed = disnake.Embed(
                        title='Ты был добавлен в вайтлист!',
                        color=disnake.Color(0x7857be),
                    )
                    embed.add_field(name='Информация о сервере', value='**Айпи:** voxirealm.fun:20024\n\n**Версия:** 1.21-1.21.1 \n\n**Рекомендуемые моды:** PlasmoVoice и NoEmoteCraft(голосовой чат и эмоции в майнкрафте). Если при установке у вас возникли какие-то вопросы, отпишите об этом нам - мы поможем!\n\n Сборку для фабрика можно скачать в канале https://discord.com/channels/1283761458215387228/1283761458819235887\n\n Если у вас не осталось вопросов, пожалуйста, закройте тикет!', inline=False)
                    await inter.send(f'<@{user_id}>', delete_after=1)
                    await inter.send(embed=embed)
                    await inter.edit_original_response(content=f'<@{user_id}> Ты был добавлен в вайтлист!')
                    await cmd_channel.send(f"Игрок {nickname} был добавлен следующим админом: {user}")
                else:
                    await inter.edit_original_response(content='⚠️Неправильно введён айди. Роль не выдана. Обязательно удалите из вайтлиста предыдущий ник, перед добавлением нового⚠️')
            else:
                await inter.edit_original_response(content=f'Ошибка при добавлении в вайтлист: {response}')
        except Exception as e:
            logger.error(f"Error in whitelist_add: {e}")
            await inter.edit_original_response(content=f'Произошла ошибка: {e}')

    @whitelist.sub_command(description='Удаляет игрока из вайтлиста', name='remove')
    @commands.has_role(config.get('whitelist_role_id'))
    async def whitelist_remove(self, inter: disnake.ApplicationCommandInteraction, nickname: str = None, user_id: str = None):
        await inter.response.defer()
        cmd_channel = self.bot.get_channel(config.get('alert_channel'))
        user = inter.user.name
        try:
            if nickname is None and user_id is None:
                await inter.edit_original_response(content='Необходимо указать либо никнейм, либо ID пользователя.')
                return

            if nickname:
                response = self._send_rcon_command_sync(f'whitelist remove {nickname}')

            elif user_id:
                async with sq.connect('whitelist.db') as db:
                    async with db.execute('SELECT nickname FROM whitelist WHERE user_id = ?', (user_id,)) as cursor:
                        row = await cursor.fetchone()
                        if row:
                            nickname = row[0]
                            response = self._send_rcon_command_sync(f'whitelist remove {nickname}')

                        else:
                            response = 'Пользователь с таким ID не найден в базе данных.'

            if 'Removed' in response:
                await remove_from_db(nickname, user_id)
                await inter.edit_original_response(content=f'{response}')
                await cmd_channel.send(f"Игрок {nickname} был `удалён` следующим админом: {user}")
            else:
                await inter.edit_original_response(content=f'Ошибка при удалении из вайтлиста: {response}')
        except Exception as e:
            logger.error(f"Error in whitelist_remove: {e}")
            await inter.edit_original_response(content=f'Произошла ошибка: {e}')

def setup(bot: commands.Bot):
    bot.add_cog(WhitelistAdder(bot))