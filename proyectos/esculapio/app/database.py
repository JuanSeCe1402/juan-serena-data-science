from contextvars import ContextVar
from pathlib import Path
from sqlalchemy import create_engine,event
from sqlalchemy.orm import sessionmaker,declarative_base
from sqlalchemy.pool import NullPool
from app.config import settings

workspace=ContextVar("demo_workspace",default=None)
Base=declarative_base()

def make_engine(url):
    args={"check_same_thread":False,"timeout":5} if url.startswith("sqlite:") else {}
    engine=create_engine(url,connect_args=args,poolclass=NullPool,hide_parameters=True)
    if url.startswith("sqlite:"):
        @event.listens_for(engine,"connect")
        def pragmas(connection,_):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=5000")
    return engine

engine=make_engine(settings.DATABASE_URL)

def SessionLocal():
    if settings.DEMO_MODE:
        path=workspace.get()
        if not path:raise RuntimeError("Demo database requires an authenticated demo workspace")
        bound=make_engine("sqlite:///"+str(path))
    else:bound=engine
    return sessionmaker(bind=bound,autoflush=False)()

def get_db():
    db=SessionLocal()
    try:yield db
    finally:db.close()
