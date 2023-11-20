import argparse
import os
import sys
from aiohttp import web
import json
import asyncio
import time


all_rows = [
    {
        "guid": str(i),
        "name": "Row %d" % i,
        "tags": "row %d" % i
    }
    for i in range(1, 250000 + 1)
]

all_tags = [row["tags"] for row in all_rows]


async def get_block(all_rows, count, start, query):
    query = query.lower()

    if args.fast:
        return fast_tree.get_block(all_rows, all_tags, count, start, query)

    rows = []
    total = 0
    for row in all_rows:
        if query == "" or row["tags"].find(query) != -1:
            if total >= start and len(rows) < count:
                rows.append(row)
            total += 1
    return {"rows": rows, "total": total}


async def index_handler(request):
    return web.FileResponse(os.path.join(app_wd, "..", "static", "index.html"))


async def get_block_handler(request):
    data = await request.json()
    t = time.time()
    block = await get_block(all_rows, data.get("count"), data["start"], data.get("query"))
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
        import fast_tree

    loop = asyncio.get_event_loop()
    loop.run_until_complete(server_init())
    loop.run_forever()
