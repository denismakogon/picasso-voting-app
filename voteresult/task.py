# 0. Read opts from STDIN
# 1. Connect to DB
# 2. Count votes

import asyncio
import collections

import json
import os
import sys

import aiopg

SELECT = "SELECT vote, COUNT(id) AS count FROM votes GROUP BY vote"


async def select_votes(pg_dns):
    result = collections.defaultdict(int)
    async with aiopg.create_pool(pg_dns) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SELECT)
                async for row in cur:
                    vote, count = row
                    result[vote] += count
                total_votes = sum(list(result.values()))
                full_result = dict(result)
                for k, v in list(full_result.items()):
                    full_result["{}_percent".format(k)] = (
                        float(v / total_votes) * 100
                        if total_votes != 0 else float(0))
                full_result['total'] = total_votes
                return full_result


if __name__ == "__main__":
    if not os.isatty(sys.stdin.fileno()):
        obj = json.loads(sys.stdin.read())
        pg_host = obj.get('pg_host')
        pg_port = obj.get('pg_port')
        pg_db = obj.get('pg_db')
        pg_user = obj.get('pg_user')
        pg_pswd = obj.get('pg_pswd')
        pg_dns = (
            'dbname={database} user={user} password={passwd} host={host}'
            .format(host=pg_host, database=pg_db, user=pg_user, passwd=pg_pswd))

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(select_votes(pg_dns))
        print(json.dumps(result))
