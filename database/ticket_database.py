import aiosqlite as sq

async def db_ticket_start():
    async with sq.connect('tickets.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ticket (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                user_id TEXT NOT NULL,
                channel_id TEXT NOT NULL
            )
        ''')
        await db.commit()

async def add_to_ticket_db(nickname, user_id, channel_id):
    async with sq.connect('tickets.db') as db:
        async with db.execute('BEGIN'):
            await db.execute('''
                INSERT INTO ticket (nickname, user_id, channel_id)
                VALUES (?, ?, ?)
            ''', (nickname, user_id, channel_id))
            await db.commit()
            
async def get_ticket_info_by_channel_id(channel_id):
    try:
        async with sq.connect('tickets.db') as db:
            async with db.execute('SELECT nickname, user_id FROM ticket WHERE channel_id = ?', (channel_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Возвращаем данные как отдельные переменные
                    nickname, user_id = row
                    return nickname, user_id
                else:
                    return None, None  # Если запись не найдена
    except Exception as e:
        print(f"Ошибка при поиске данных по channel_id: {e}")
        return None, None

### Желательно бы потом чистить старые тикеты??