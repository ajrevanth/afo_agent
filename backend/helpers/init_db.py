"""
Create (or recreate) the application database schema.

Usage:

    cd backend && python -m helpers.init_db                 # create tables if missing
    cd backend && python -m helpers.init_db --drop          # drop all and recreate
    cd backend && python -m helpers.init_db --seed-admin    # create tables + seed admin user
    python backend/helpers/init_db.py                       # equivalent from repo root

Reads DATABASE_URL from env, falling back to the docker-compose default.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from helpers.schema import Base, UserORM
from helpers.auth import hash_password

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/afo"


def get_engine(echo: bool = False) -> Engine:
    url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    return create_engine(url, echo=echo, future=True)


def create_all(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
    print(f"[init_db] created tables: {', '.join(sorted(Base.metadata.tables.keys()))}")


def drop_all(engine: Engine) -> None:
    Base.metadata.drop_all(bind=engine)
    print("[init_db] dropped all tables")


def seed_admin(engine: Engine, username: str, email: str, password: str) -> None:
    Session = sessionmaker(bind=engine)
    with Session() as db:
        existing = db.query(UserORM).filter(UserORM.username == username).first()
        if existing:
            print(f"[init_db] admin user '{username}' already exists, skipping")
            return
        db.add(UserORM(
            username=username,
            email=email,
            password_hash=hash_password(password),
        ))
        db.commit()
        print(f"[init_db] seeded admin user '{username}'")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize the AFO application database.")
    parser.add_argument("--drop", action="store_true", help="Drop all tables before creating.")
    parser.add_argument("--echo", action="store_true", help="Echo SQL to stdout.")
    parser.add_argument("--seed-admin", action="store_true", help="Seed a default admin user.")
    parser.add_argument("--admin-username", default=os.environ.get("ADMIN_USERNAME", "admin"))
    parser.add_argument("--admin-email", default=os.environ.get("ADMIN_EMAIL", "admin@example.com"))
    parser.add_argument("--admin-password", default=os.environ.get("ADMIN_PASSWORD", "changeme"))
    args = parser.parse_args(argv)

    engine = get_engine(echo=args.echo)

    if args.drop:
        drop_all(engine)

    create_all(engine)

    if args.seed_admin:
        seed_admin(engine, args.admin_username, args.admin_email, args.admin_password)

    return 0


if __name__ == "__main__":
    sys.exit(main())
