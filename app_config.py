import logging
import os
import dotenv
import redis
from flask_uuid import FlaskUUID
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import faker
from celery import Celery
from flask import Flask
dotenv.load_dotenv()

flask_app = Flask(__name__)
FlaskUUID(flask_app)
celery_app = Celery(broker=os.getenv("REDIS_CELERY_URL"))
redis_conn = redis.Redis.from_url(os.getenv("REDIS_URL"))
fake = faker.Faker()
logging.basicConfig(level="INFO")
logger = logging.getLogger("geo_redis")

engine = create_engine(
    os.path.join(os.getenv("POSTGRES_URL"), os.getenv("DATABASE_NAME")),
    pool_size=10,
    max_overflow=20
)
base = declarative_base(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()