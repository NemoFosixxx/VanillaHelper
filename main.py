import disnake
from disnake.ext import commands
import yaml
command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True

bot = commands.Bot(command_prefix='!', test_guilds=[1217058758862307348], command_sync_flags=command_sync_flags, intents=disnake.Intents.all()) #test_guilds=[ 1283761458215387228]



@bot.event                  
async def on_ready():
    print('Бот запущен!')
    

bot.load_extensions("core/cogs") #Инициализация когов йоу

file_path = 'config.yml'
with open(file_path, 'r') as file:
    config = yaml.safe_load(file)
TOKEN = config.get('token')
bot.run(TOKEN)