# 0. Read parameters from STDIN
# 1. Connect to database
# 2. Create table if not exists
# 3. Insert new vote
# 4. If vote exists, update

import aiopg
import asyncio
import json
import os
import sys


CREATE = ("CREATE TABLE IF NOT EXISTS votes (id VARCHAR(255) "
          "NOT NULL UNIQUE, vote VARCHAR(255) NOT NULL)")
INSERT = "INSERT INTO votes (id, vote) VALUES ('{}', '{}')"
UPDATE = "UPDATE votes SET id = '{}' WHERE vote = '{}'"


async def run_vote(pg_dns, vote_id, vote):
    async with aiopg.create_pool(pg_dns) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(CREATE)
                    await cur.execute(INSERT.format(vote_id, vote))
                except Exception as ex1:
                    try:
                        await cur.execute(UPDATE.format(vote_id, vote))
                    except Exception as ex2:
                        print("Original exception: {}. Update attempt: {}"
                              .format(str(ex1), str(ex2)))


if __name__ == "__main__":
    if not os.isatty(sys.stdin.fileno()):
        obj = json.loads(sys.stdin.read())
        pg_host = obj.get('pg_host')
        pg_port = obj.get('pg_port')
        pg_db = obj.get('pg_db')
        pg_user = obj.get('pg_user')
        pg_pswd = obj.get('pg_pswd')
        vote_id = obj.get('vote_id')
        vote = obj.get('vote')

        pg_dns = (
            'dbname={database} user={user} password={passwd} host={host}'
            .format(host=pg_host, database=pg_db, user=pg_user, passwd=pg_pswd))

        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_vote(pg_dns, vote_id, vote))
