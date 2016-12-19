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
        pg_dns = obj.get('pg_dns')
        vote_id = obj.get('vote_id')
        vote = obj.get('vote')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_vote(pg_dns, vote_id, vote))
