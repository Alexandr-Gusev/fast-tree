import argparse
import os
import sys
from aiohttp import web
import asyncio
import time


rows = [
    {
        "id": str(i),
        "name": "Row %d" % i
    }
    for i in range(1, 250000 + 1)
]

keys_for_search = [row["name"].lower() for row in rows]


async def get_block(rows, block_size, block_start, query):
    query = query.lower()

    if args.fast:
        return fast_tree_utils.get_block(rows, keys_for_search, block_size, block_start, query)

    block_rows = []
    total = 0
    for i, row in enumerate(rows):
        if query == "" or keys_for_search[i].find(query) != -1:
            if total >= block_start and len(block_rows) < block_size:
                block_rows.append(row)
            total += 1
    return {"rows": block_rows, "total": total}


async def index_handler(request):
    return web.FileResponse(os.path.join(app_wd, "..", "static", "index.html"))


async def get_block_handler(request):
    data = await request.json()
    t = time.time()
    block = await get_block(rows, data.get("block_size"), data["block_start"], data.get("query"))
    print("dt: %d ms" % int((time.time() - t) * 1000))
    return web.json_response(block)


async def server_init():
    app = web.Application()
    app.add_routes([
        web.get("/", index_handler),
        web.static("/static", os.path.join(app_wd, "..", "static")),
        web.post("/get-block", get_block_handler),
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.addr, args.port)
    await site.start()


if __name__ == "__main__":
    app_wd = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser()
    parser.add_argument("--addr", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--fast", action='store_true')
    args = parser.parse_args()

    if args.fast:
        import fast_tree_utils

    loop = asyncio.get_event_loop()
    loop.run_until_complete(server_init())
    loop.run_forever()
