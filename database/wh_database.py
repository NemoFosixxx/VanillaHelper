import aiosqlite as sq

async def db_start():
    async with sq.connect('whitelist.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                user_id TEXT NOT NULL
            )
        ''')
        await db.commit()
        
async def add_to_db(nickname, user_id):
    async with sq.connect('whitelist.db') as db:
        async with db.execute('BEGIN'):
            await db.execute('''
                INSERT INTO whitelist (nickname, user_id)
                VALUES (?, ?)
            ''', (nickname, user_id))
            await db.commit()

async def remove_from_db(nickname=None, user_id=None):
    async with sq.connect('whitelist.db') as db:
        async with db.execute('BEGIN'):
            if nickname:
                await db.execute('''
                    DELETE FROM whitelist WHERE nickname = ?
                ''', (nickname,))
            if user_id:
                async with db.execute('SELECT nickname FROM whitelist WHERE user_id = ?', (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        nickname = row[0]
                        await db.execute('''
                            DELETE FROM whitelist WHERE nickname = ?
                        ''', (nickname,))
            await db.commit()
            
async def list_user_id(nickname, user_id):
    async with sq.connect('whitelist.db') as db:
        async with db.execute('BEGIN'):
            await db.execute('''
                SELECT nickname FROM whitelist WHERE nickname = ?''', (nickname, user_id))
            await db.commit()