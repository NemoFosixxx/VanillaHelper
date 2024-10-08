import disnake
import logging
import yaml
from disnake.ext import commands
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подгруз конфигов
file_path = 'config.yml'
with open(file_path, 'r') as file:
    config = yaml.safe_load(file)

class MenuForming(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.whitelist_support = config.get('whitelist_role_id')

    @commands.slash_command(description="Создаёт эмбед с выпадающим меню для обращений", name="menu")
    @commands.has_role(config.get('bot_admin'))
    async def setup_menu(self, inter: disnake.ApplicationCommandInteraction):
        embed = disnake.Embed(
            title="Открыть обращение",
            description="Для того чтобы открыть обращение, выберите тип обращения в меню ниже.",
            color=disnake.Color(0x7857be)
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/415752039713472513/1288380944717447178/Frame_18_1.png?ex=670228c2&is=6700d742&hm=387109f6dcd11a5df2995486fcbab12dbd9e33bad1f724730553ad45487d6487&")

        select_menu = disnake.ui.Select(
            custom_id="complaint_menu",
            options=[
                disnake.SelectOption(label="Жалоба на игрока", value="complaint_player", description="Подать жалобу на игрока", emoji="⚠️"),
                disnake.SelectOption(label="Жалоба на администрацию", value="complaint_admin", description="Подать жалобу на администрацию", emoji="⚠️"),
                disnake.SelectOption(label="Вопрос к администрации", value="admin_question", description="Задать вопрос администрации", emoji="❓"),
                disnake.SelectOption(label="Предложение по улучшению", value="suggestion", description="Предложить улучшения", emoji="💡")
            ],
            placeholder="Выберите тип обращения",
            min_values=1,
            max_values=1
        )

        await inter.send(embed=embed, components=[disnake.ui.ActionRow(select_menu)])

    @commands.Cog.listener()
    async def on_message_interaction(self, inter: disnake.MessageInteraction):
        if inter.data.custom_id == "complaint_menu":
            selected_option = inter.data.values[0]
            
            if selected_option == "complaint_player":
                modal = disnake.ui.Modal(
                    title="Жалоба на игрока",
                    custom_id="complaint_player",
                    components=[
                        disnake.ui.TextInput(
                            label="Ваш ник в Майнкрафт",
                            custom_id="nickname",
                            style=disnake.TextInputStyle.short,
                            max_length=16,
                            required=True
                        ),
                        disnake.ui.TextInput(
                            label="Ник нарушителя",
                            custom_id="griefer",
                            style=disnake.TextInputStyle.short,
                            required=True
                        ),
                        disnake.ui.TextInput(
                            label="Пункт нарушения",
                            custom_id="point",
                            style=disnake.TextInputStyle.paragraph,
                            required=True
                        ),
                        disnake.ui.TextInput(
                            label="Описание нарушения",
                            custom_id="description",
                            style=disnake.TextInputStyle.paragraph,
                            required=True
                        )
                    ]
                )
                await inter.response.send_modal(modal)

            elif selected_option == "complaint_admin":
                modal = disnake.ui.Modal(
                    title="Жалоба на администрацию",
                    custom_id="complaint_admin",
                    components=[
                        disnake.ui.TextInput(
                            label="Ваш ник в Майнкрафт",
                            custom_id="nickname",
                            style=disnake.TextInputStyle.short,
                            max_length=16,
                            required=True
                        ),
                        disnake.ui.TextInput(
                            label="Ник нарушившего админа",
                            custom_id="admin_nickname",
                            style=disnake.TextInputStyle.short,
                            required=True
                        ),
                        disnake.ui.TextInput(
                            label="Описание нарушения",
                            custom_id="description",
                            style=disnake.TextInputStyle.paragraph,
                            required=True
                        )
                    ]
                )
                await inter.response.send_modal(modal)

            elif selected_option == "admin_question":
                modal = disnake.ui.Modal(
                    title="Вопрос к администрации",
                    custom_id="admin_question",
                    components=[
                        disnake.ui.TextInput(
                            label="Ваш ник в Майнкрафт",
                            custom_id="nickname",
                            style=disnake.TextInputStyle.short,
                            max_length=16,
                            required=True
                        ),
                        disnake.ui.TextInput(
                            label="Ваш вопрос",
                            custom_id="question",
                            style=disnake.TextInputStyle.paragraph,
                            required=True
                        )
                    ]
                )
                await inter.response.send_modal(modal)

            elif selected_option == "suggestion":
                modal = disnake.ui.Modal(
                    title="Предложение по улучшению",
                    custom_id="suggestion",
                    components=[
                        disnake.ui.TextInput(
                            label="Ваш ник в Майнкрафт",
                            custom_id="nickname",
                            style=disnake.TextInputStyle.short,
                            max_length=16,
                            required=True
                        ),
                        disnake.ui.TextInput(
                            label="Ваше предложение",
                            custom_id="suggest",
                            style=disnake.TextInputStyle.paragraph,
                            required=True
                        )
                    ]
                )
                await inter.response.send_modal(modal)
                
    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        if inter.custom_id == "complaint_player":
            nickname = inter.text_values["nickname"]
            griefer = inter.text_values["griefer"]
            point = inter.text_values["point"]
            description = inter.text_values["description"]
            user = inter.user
            self.user_button_id = str(user.id)
            self.button_nickname = nickname
            category = disnake.utils.get(inter.guild.categories, name="Жалобы на игроков")
            if category is None:
                category = await inter.guild.create_category("Жалобы на игроков")
            whitelist_role = inter.guild.get_role(config.get('whitelist_role_id'))
            
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

            complaint_player_channel = await inter.guild.create_text_channel(name=f'ticket-{user.name}', category=category, overwrites=overwrites)
            complaint_player_channel_id = complaint_player_channel.id
            
            await inter.send(f'Твой тикет был создан! <#{complaint_player_channel_id}>', ephemeral=True)
            await complaint_player_channel.send(f'{user.mention} <@&{self.whitelist_support}>', delete_after=1)
            
            complaint_player_embed = disnake.Embed(
                title='Жалоба на игрока',
                description = "Ваш тикет скоро будет рассмотрен! Обычно это не занимает много времени.",
                color=disnake.Color(0x7857be) 
            )
            complaint_player_embed.add_field(name="Ник в Майнкрафте", value=nickname, inline=False)
            complaint_player_embed.add_field(name="Ник нарушителя", value=griefer, inline=False)
            complaint_player_embed.add_field(name="Пункт", value=point, inline=False)
            complaint_player_embed.add_field(name="Описание ситуации", value=description, inline=False)
            message = await complaint_player_channel.send(embed=complaint_player_embed, components=[
                disnake.ui.Button(label="Закрыть тикет", custom_id="close_ticket_menu", style=disnake.ButtonStyle.danger)
            ])
            await message.pin()
        
        elif inter.custom_id == "complaint_admin":
            nickname = inter.text_values["nickname"]
            admin_nickname = inter.text_values["admin_nickname"]
            description = inter.text_values["description"]
            user = inter.user
            self.user_button_id = str(user.id)
            self.button_nickname = nickname
            category = disnake.utils.get(inter.guild.categories, name="Жалобы на админов")
            if category is None:
                category = await inter.guild.create_category("Жалобы на админов")
            whitelist_role = inter.guild.get_role(config.get('whitelist_role_id'))
            
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

            complaint_admin_channel = await inter.guild.create_text_channel(name=f'ticket-{user.name}', category=category, overwrites=overwrites)
            complaint_admin_channel_id = complaint_admin_channel.id
            
            await inter.send(f'Твой тикет был создан! <#{complaint_admin_channel_id}>', ephemeral=True)
            await complaint_admin_channel.send(f'{user.mention} <@&{self.whitelist_support}>', delete_after=1)
            
            complaint_admin_embed = disnake.Embed(
                title='Жалоба на админа',
                description = "Ваш тикет скоро будет рассмотрен! Обычно это не занимает много времени.",
                color=disnake.Color(0x7857be) 
            )
            complaint_admin_embed.add_field(name="Ник в Майнкрафте", value=nickname, inline=False)
            complaint_admin_embed.add_field(name="Ник админа", value=admin_nickname, inline=False)
            complaint_admin_embed.add_field(name="Описание ситуации", value=description, inline=False)
            message = await complaint_admin_channel.send(embed=complaint_admin_embed, components=[
                disnake.ui.Button(label="Закрыть тикет", custom_id="close_ticket_menu", style=disnake.ButtonStyle.danger)
            ])
            await message.pin()
        
        elif inter.custom_id == "admin_question":
            nickname = inter.text_values["nickname"]
            question = inter.text_values["question"]
            user = inter.user
            self.user_button_id = str(user.id)
            self.button_nickname = nickname
            category = disnake.utils.get(inter.guild.categories, name="Вопросы")
            if category is None:
                category = await inter.guild.create_category("Вопросы")
            whitelist_role = inter.guild.get_role(config.get('whitelist_role_id'))
            
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

            question_channel = await inter.guild.create_text_channel(name=f'ticket-{user.name}', category=category, overwrites=overwrites)
            question_channel_id = question_channel.id
            await inter.send(f'Твой тикет был создан! <#{question_channel_id}>', ephemeral=True)
            await question_channel.send(f'{user.mention} <@&{self.whitelist_support}>', delete_after=1)
            
            question_embed = disnake.Embed(
                title="Вопрос к админам",
                description= "Ваш вопрос скоро будет рассмотрен! Обычно это не занимает много времени.",
                color=disnake.Color(0x7857be)
            )
            question_embed.add_field(name="Ник в Майнкрафте", value=nickname, inline=False)
            question_embed.add_field(name="Вопрос", value=question, inline=False)
            message = await question_channel.send(embed=question_embed, components=[
                disnake.ui.Button(label="Закрыть тикет", custom_id="close_ticket_menu", style=disnake.ButtonStyle.danger)
            ])
            await message.pin()
        
        elif inter.custom_id == "suggestion":
            nickname = inter.text_values["nickname"]
            suggest = inter.text_values["suggest"]
            user = inter.user
            self.user_button_id = str(user.id)
            self.button_nickname = nickname
            category = disnake.utils.get(inter.guild.categories, name="Предложения")
            if category is None:
                category = await inter.guild.create_category("Предложения")
            whitelist_role = inter.guild.get_role(config.get('whitelist_role_id'))
            
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
            suggestion_channel = await inter.guild.create_text_channel(name=f'ticket-{user.name}', category=category, overwrites=overwrites)
            suggestion_channel_id = suggestion_channel.id
            await inter.send(f'Твой тикет был создан! <#{suggestion_channel_id}>', ephemeral=True)
            await suggestion_channel.send(f'{user.mention} <@&{self.whitelist_support}>', delete_after=1)
            
            suggestion_embed = disnake.Embed(
                title="Предложение",
                description = "Ваше предложение скоро будет рассмотрено! Обычно это не занимает много времени.",
                color=disnake.Color(0x7857be)
            )
            suggestion_embed.add_field(name="Ник в Майнкрафте", value=nickname, inline=False)
            suggestion_embed.add_field(name="Предложение", value=suggest, inline=False)
            message = await suggestion_channel.send(embed=suggestion_embed, components=[
                disnake.ui.Button(label="Закрыть тикет", custom_id="close_ticket_menu", style=disnake.ButtonStyle.danger)
            ])
            await message.pin()
            
    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        try:
            if inter.component.custom_id == "close_ticket_menu":
                whitelist_role_id = config.get('whitelist_role_id')
                if any(role.id == int(whitelist_role_id) for role in inter.user.roles):
                    user = inter.user.name
                    channel = inter.channel.name
                    cmd_channel = self.bot.get_channel(config.get('alert_channel'))
                    await cmd_channel.send(f"Тикет {channel} был `закрыт` следующим админом: {user}")
                    await inter.send("Тикет будет удалён через 3 секунды...")
                    await asyncio.sleep(3)

                    await inter.channel.delete()
                else:
                    await inter.send("У вас нет прав на использование этой кнопки", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in on_button_click: {e}")
            await inter.send("Произошла ошибка при обработке взаимодействия", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(MenuForming(bot))
