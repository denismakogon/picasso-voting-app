# 0. Read parameters from STDIN
# 1. connect to database
# 2. Create table
# CREATE TABLE IF NOT EXISTS votes (id VARCHAR(255) NOT NULL UNIQUE, vote VARCHAR(255) NOT NULL)
# 3. Insert new vote
# INSERT INTO votes (id, vote) VALUES (?, ?)
# 4. If vote exists, update
# UPDATE votes SET vote = ? WHERE id = ?

import asyncio
import collections

import json
import os
import sys

import aiopg

CREATE = ("CREATE TABLE IF NOT EXISTS votes (id VARCHAR(255) "
          "NOT NULL UNIQUE, vote VARCHAR(255) NOT NULL)")
INSERT = "INSERT INTO votes (id, vote) VALUES ({}, {})"


async def query(pg_dns, sql_query):
    result = collections.defaultdict(int)
    async with aiopg.create_pool(pg_dns) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql_query)
                async for row in cur:
                    vote, count = row
                    result[vote] += count


if __name__ == "__main__":
    if not os.isatty(sys.stdin.fileno()):
        obj = json.loads(sys.stdin.read())
        pg_dns = obj.get('pg_dns')
        vote_id = obj.get('vote_id')
        vote = obj.get('vote')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(query(pg_dns, CREATE))
        loop.run_until_complete(
            query(pg_dns, INSERT.format(vote_id, vote)))
