import os

from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app_config import engine, logger, base, session, fake
from models import ProfileModel

class ScenarioBuilder:

    def __init__(self):
        logger.info(f"Scenario Builder execute")
        ScenarioBuilder.create_database()
        ScenarioBuilder.create_extension_postgis()
        ScenarioBuilder.create_model()
        ScenarioBuilder.populate_model()

    @staticmethod
    def create_database():
        # remove database name from string connection before create the new schema
        tmp_engine = create_engine(os.path.join(os.getenv("POSTGRES_URL"), "postgres"), echo=False)
        with tmp_engine.connect() as conn:
            conn.execute("commit")
            try:
                conn.execute(f"CREATE DATABASE {os.getenv('DATABASE_NAME')} WITH OWNER postgres TABLESPACE pg_default")
                logger.info(f"Database {os.getenv('DATABASE_NAME')} created")
            except ProgrammingError as ex:
                logger.error(ex)

    @staticmethod
    def create_extension_postgis():
        with engine.connect() as conn:
            conn.execute(f"CREATE EXTENSION IF NOT EXISTS postgis")
            logger.info(f"Instalação da extensão postgis")


    @staticmethod
    def create_model():
        try:
            base.metadata.create_all(engine)
            logger.info(f"Models profile created")
        except Exception as ex:
            logger.info(f"Models profile already created")

    @staticmethod
    def insert_bulk(data, i):
        session_t = Session()
        logger.info(f"Inserting {len(data)} profiles in bulk ({i})")
        session_t.bulk_insert_mappings(ProfileModel, data)
        session_t.commit()
        session_t.close()
        engine.dispose()

    @staticmethod
    def populate_model(count=1000000):

        data = []
        for i in range(count):
            data.append(ScenarioBuilder.build_fake())

            if i % 10000 == 0:
                ScenarioBuilder.insert_bulk(data, i)
                data = []
                logger.info(f"Loading fake data index({i})")

        session.bulk_insert_mappings(ProfileModel, data)

    @staticmethod
    def build_fake():
        latlng = fake.local_latlng()
        return dict(
            name=fake.name(),
            occupation=fake.job(),
            company_email=fake.company_email(),
            credit_card_provider=fake.credit_card_provider(),
            phone_number=fake.phone_number(),
            date_of_birth=fake.date_of_birth().isoformat(),
            city=latlng[2],
            tz=latlng[4],
            latitude=float(latlng[0]),
            longitude=float(latlng[1])
        )


if __name__ == "__main__":
    ScenarioBuilder()
