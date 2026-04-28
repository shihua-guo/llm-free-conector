import argparse
import asyncio

from app.db.init import init_db
from app.db.session import SessionLocal
from app.services.newapi_client import NewAPIClient
from app.services.sync import ModelSyncService


async def sync_once() -> None:
    await init_db()
    async with SessionLocal() as session:
        client = NewAPIClient()
        service = ModelSyncService(session, client)
        summary = await service.sync()
        print(summary)


def main() -> None:
    parser = argparse.ArgumentParser(prog="llm-free-conector")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("sync", help="Sync NewAPI channels and models once")
    args = parser.parse_args()

    if args.command == "sync":
        asyncio.run(sync_once())


if __name__ == "__main__":
    main()
