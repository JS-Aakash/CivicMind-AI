import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app.api.routes.command_center import get_command_center_overview
from app.db.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as s:
        res = await get_command_center_overview(s)
        print("RESULT SUCCESS:", res["kpis"])

if __name__ == "__main__":
    asyncio.run(main())
