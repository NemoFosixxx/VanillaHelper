import disnake
import aiosqlite as sq
import asyncio
from disnake.ext import commands
import yaml
import logging
from mcrcon import MCRcon
from database.wh_database import add_to_db
from database.ticket_database import add_to_ticket_db, db_ticket_start, get_ticket_info_by_channel_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подгруз конфигов
file_path = 'config.yml'
with open(file_path, 'r') as file:
    config = yaml.safe_load(file)

class TicketsForming(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.db_ticket_start())
        self.whitelist_support = config.get('whitelist_role_id')
        self.category_wh = "Whitelist"
        self.category_complaints = "Жалобы"
        self.button_nickname = None
        self.user_button_id = None
        
    async def db_ticket_start(self):
        try:
            await db_ticket_start()
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

    @commands.slash_command(description="Создаёт эмбед с кнопкой для тикетов", name='setup')
    @commands.has_role(config.get('bot_admin'))
    async def setup(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @setup.sub_command(description="Создаёт эмбед для подачи заявки и категорию с тикетами, если её нет", name="whitelist")
    @commands.has_role(config.get('bot_admin'))
    async def setup_whitelist(self, inter: disnake.ApplicationCommandInteraction):
        # Создание категории, если она отсутствует
        category_wh = self.category_wh
        category = disnake.utils.get(inter.guild.categories, name=category_wh)
        if category is None:
            category = await inter.guild.create_category(name=category_wh)

        # Вызов эмбеда
        embed = disnake.Embed(
            title='Заявка на сервер',
            description='Для того чтобы начать играть на нашем сервере, тебе нужно подать заявку. Жмякни кнопку ниже!',
            color=disnake.Color(0x7857be)
        )
        embed.set_image(url='https://cdn.discordapp.com/attachments/415752039713472513/1288380944717447178/Frame_18_1.png?ex=66f4f9c2&is=66f3a842&hm=b646da682098763bd4e98f6f49c27f13af6004e4e2f33f6aa547ae6563d9dd5a&')
        await inter.send(
            embed=embed,
            components=[
                disnake.ui.Button(label="💖 Подать заявку на сервер!", style=disnake.ButtonStyle.success, custom_id="open"),
            ],
        )

    @commands.Cog.listener()
    async def on_interaction(self, inter: disnake.Interaction):
        if inter.type == disnake.InteractionType.component:
            if inter.component.custom_id == "open":
                # Открытие модального окна при нажатии кнопки
                modal = disnake.ui.Modal(
                    title="Подача заявки",
                    custom_id="whitelist_form",
                    components=[
                        disnake.ui.TextInput(
                            label="НИК В МАЙНКРАФТЕ",
                            placeholder="Максимальная длина ника - 16 символов.",
                            custom_id="nickname",
                            style=disnake.TextInputStyle.short,
                            max_length=16,
                            required=True
                        ),
                        disnake.ui.TextInput(
                            label="ЧЕМ ПЛАНИРУЕТЕ ЗАНИМАТЬСЯ НА СЕРВЕРЕ?",
                            placeholder="Если не знаете - так и пишите.",
                            custom_id="plans",
                            style=disnake.TextInputStyle.paragraph,
                            required=True,
                        ),
                        disnake.ui.TextInput(
                            label="КАК ВЫ НАШЛИ ЭТОТ СЕРВЕР?",
                            placeholder="Через друзей, видео/шортс и т.п. Нам это правда важно!",
                            custom_id="search",
                            style=disnake.TextInputStyle.paragraph,
                            required=True,
                        )
                    ]
                )
                await inter.response.send_modal(modal)
                
            elif inter.component.custom_id == "open_complaints":
                complaints_modal = disnake.ui.Modal(
                    title="Подача обращения",
                    custom_id="complaints_form",
                    components=[
                        disnake.ui.TextInput(
                            label="НИК В МАЙНКРАФТЕ",
                            custom_id="nickname",
                            style=disnake.TextInputStyle.short,
                            max_length=16,
                            required=True
                        ),
                        disnake.ui.TextInput(
                            label="НИКНЕЙМ НАРУШИТЕЛЯ",
                            placeholder="Если не нужен, ставьте прочерк",
                            custom_id="griefer",
                            style=disnake.TextInputStyle.paragraph,
                            required=True
                        ),
                        disnake.ui.TextInput(
                            label="ВАШ ВОПРОС/ЧТО СЛУЧИЛОСЬ",
                            custom_id="question",
                            style=disnake.TextInputStyle.paragraph,
                            required=True
                        )
                    ]
                )
                await inter.response.send_modal(complaints_modal)
                        
    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        if inter.custom_id == "whitelist_form":
            nickname = inter.text_values["nickname"]
            plans = inter.text_values["plans"]
            search = inter.text_values["search"]
            user = inter.user
            self.user_button_id = str(user.id)
            self.button_nickname = nickname
            category_wh = self.category_wh
            category = disnake.utils.get(inter.guild.categories, name=category_wh)
            if category is None:
                category = await inter.guild.create_category(name=category_wh)

            whitelist_role = inter.guild.get_role(self.whitelist_support)

            overwrites = {
                inter.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
                user: disnake.PermissionOverwrite(
                    read_messages=True, send_messages=True, add_reactions=True, 
                    embed_links=True, attach_files=True, read_message_history=True,
                    external_emojis=True
                ),
                whitelist_role: disnake.PermissionOverwrite(
                    read_messages=True, send_messages=True, add_reactions=True, 
                    embed_links=True, attach_files=True, read_message_history=True,
                    external_emojis=True
                )
            }

            
            whitelist_channel = await inter.guild.create_text_channel(name=f'ticket-{user.name}', category=category, overwrites=overwrites)
            whitelist_channel_id = whitelist_channel.id


            await inter.send(f'Твой тикет был создан! <#{whitelist_channel_id}>', ephemeral=True)
            await whitelist_channel.send(f'{user.mention} <@&{self.whitelist_support}>', delete_after=1)

            embed2 = disnake.Embed(
                title='Спасибо за подачу заявки!',
                description='Ваша заявка скоро будет рассмотрена! Обычно это занимает не более часа.',
                color=disnake.Color(0x7857be)
            )
            embed2.add_field(name="Ник в Майнкрафте", value=nickname, inline=False)
            embed2.add_field(name="Чем планируете заниматься на сервере?", value=plans, inline=False)
            embed2.add_field(name="Как вы нашли этот сервер?", value=search, inline=False)

            message = await whitelist_channel.send(embed=embed2, components=[
                disnake.ui.Button(label="Добавить в вайтлист", style=disnake.ButtonStyle.primary, custom_id="whitelist_add"),
                disnake.ui.Button(label="Закрыть тикет", style=disnake.ButtonStyle.danger, custom_id="close_ticket")
            ])
            await message.pin()
            
            #Сохранение данных в бд
            try:
                await add_to_ticket_db(nickname=nickname, user_id=user.id, channel_id=whitelist_channel_id)
            except Exception as e:
                await inter.send(f"Ошибка при добавлении в базу данных: {e}", ephemeral=True)
            

        elif inter.custom_id == "complaints_form":
            nickname = inter.text_values["nickname"]
            griefer = inter.text_values["griefer"]
            question = inter.text_values["question"]
            user = inter.user
            self.user_button_id = str(user.id)
            self.button_nickname = nickname
            category_complaints = self.category_complaints
            category = disnake.utils.get(inter.guild.categories, name=category_complaints)
            if category is None:
                category = await inter.guild.create_category(name=category_complaints)
                
            whitelist_role = inter.guild.get_role(self.whitelist_support)

            overwrites = {
                inter.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
                user: disnake.PermissionOverwrite(
                    read_messages=True, send_messages=True, add_reactions=True, 
                    embed_links=True, attach_files=True, read_message_history=True,
                    external_emojis=True
                ),
                whitelist_role: disnake.PermissionOverwrite(
                    read_messages=True, send_messages=True, add_reactions=True, 
                    embed_links=True, attach_files=True, read_message_history=True,
                    external_emojis=True
                )
            }
            
            complaint_channel = await inter.guild.create_text_channel(name=f'ticket-{user.name}', category=category, overwrites=overwrites)
            complaint_channel_id = complaint_channel.id
            
            await inter.send(f'Твой тикет был создан! <#{complaint_channel_id}>', ephemeral=True)
            await complaint_channel.send(f'{user.mention} <@&{self.whitelist_support}>', delete_after=1)
            
            embed2 = disnake.Embed(
                title="Обращение открыто!",
                description="Ваш тикет скоро будет рассмотрен! Обычно это не занимает много времени.",
                color=disnake.Color(0x7857be)
            )
            embed2.add_field(name="Ник в Майнкрафте", value=nickname, inline=False)
            embed2.add_field(name="Ник нарушителя", value=griefer, inline=False)
            embed2.add_field(name="Что произошло/Вопрос", value=question, inline=False)
            
            message = await complaint_channel.send(embed=embed2, components=[
                disnake.ui.Button(label="Закрыть тикет", style=disnake.ButtonStyle.danger, custom_id="close_ticket_complaints")
            ])
            await message.pin()

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        try:
            if inter.component.custom_id == "close_ticket_complaints":
                if any(role.id == config.get('whitelist_role_id') for role in inter.user.roles):
                    user = inter.user.name
                    channel = inter.channel.name
                    cmd_channel = self.bot.get_channel(config.get('alert_channel'))
                    await cmd_channel.send(f"Тикет {channel} был `закрыт` следующим админом: {user}")
                    await inter.send("Тикет будет удалён через 3 секунды...")
                    await asyncio.sleep(3)
                    await inter.channel.delete()
                else:
                    await inter.send("У вас нет прав на использование этой кнопки", ephemeral=True)
    
            elif inter.component.custom_id == "close_ticket":
                await inter.send("Тикет будет удалён через 3 секунды...")
                await asyncio.sleep(3)
                await inter.channel.delete()
                
            elif inter.component.custom_id == "whitelist_add":
                logger.info(f"Whitelist add button clicked by user {inter.user.id} ({inter.user.name})")
                #ЗДЕСЬ НАДО ИЗ БД БРАТЬ ДАННЫЕ. ИСКАТЬ АЙДИ КАНАЛА СРЕДИ БД ТИКЕТОВ
                if any(role.id == config.get('whitelist_role_id') for role in inter.user.roles):
                    channel_id = inter.channel.id
                    nickname, user_id = await get_ticket_info_by_channel_id(channel_id)

                    if nickname is None:
                        await inter.send('Поле с ником отсутствует, либо бот был перезагружен. Пожалуйста, используйте ручное добавление `/whitelist add`', ephemeral=True)
                        return

                    cmd_channel = self.bot.get_channel(config.get('alert_channel'))
                    user = inter.user.name
                    try:
                        async with sq.connect('whitelist.db') as db:
                            async with db.execute('SELECT nickname FROM whitelist WHERE user_id = ?', (user_id,)) as cursor:
                                row = await cursor.fetchone()
                                if row:
                                    await inter.send(content=f'Пользователь с Discord ID {user_id} уже привязан к нику {row[0]}.', ephemeral=True)
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

                        await inter.response.send_message("Пользователь добавлен в вайтлист!", ephemeral=True)
                    except Exception as e:
                        logger.error(f"Error in whitelist_add: {e}")
                        await inter.edit_original_response(content=f'Произошла ошибка: {e}')
                    finally:
                        self.button_nickname = None
                        self.user_button_id = None
                else:
                    await inter.send("У вас нет прав на использование этой кнопки", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in on_button_click: {e}")
            await inter.send("Произошла ошибка при обработке взаимодействия", ephemeral=True)
            
    @setup.sub_command(description="Создаёт эмбед для подачи заявки и категорию с тикетами, если её нет", name="complaints")
    @commands.has_role(config.get('bot_admin'))
    async def setup_complaints(self, inter: disnake.ApplicationCommandInteraction):
        category_complaints = self.category_complaints
        category = disnake.utils.get(inter.guild.categories, name=category_complaints)
        if category is None:
            category = await inter.guild.create_category(name=category_complaints)
        
        embed = disnake.Embed(
            title='Подача жалобы/ Вопроса к админам',
            description='Для того чтобы открыть обращение, нажмите кнопку ниже!',
            color=disnake.Color(0x7857be)
        )
        embed.set_image(url='https://cdn.discordapp.com/attachments/415752039713472513/1288382655418859564/xbouw053Prs.jpg?ex=66f4fb5a&is=66f3a9da&hm=1bfdf0b9e19a1f202accda11cd96f0f27785dde3ee977ad36fbd19c3e1fcb61c&')
        await inter.send(
            embed=embed,
            components=[
                disnake.ui.Button(label="📃 Открыть обращение", style=disnake.ButtonStyle.success, custom_id="open_complaints"),
            ],
        )

def setup(bot: commands.Bot):
    bot.add_cog(TicketsForming(bot))