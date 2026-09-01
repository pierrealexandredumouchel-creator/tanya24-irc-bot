#!/usr/bin/env python3
# Tanya24 IRC Bot - Command & Conquer Edition
import asyncio, aiohttp, os
from dotenv import load_dotenv
load_dotenv()

async def main():
    print("Tanya24 online. Ready for orders, Commander alxd.")
    # TODO: connect to IRC, handle events, AI responses

if __name__ == "__main__":
    asyncio.run(main())
