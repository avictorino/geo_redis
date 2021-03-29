import json
import uuid
from sqlalchemy import Column, String, Float
from sqlalchemy.dialects.postgresql import UUID

from app_config import base, engine


class ProfileModel(base):
    __tablename__ = "profile"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    occupation = Column(String(255), nullable=True)
    company_email = Column(String(255), nullable=True)
    credit_card_provider = Column(String(255), nullable=True)
    phone_number = Column(String(255), nullable=True)
    date_of_birth = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    tz = Column(String(255), nullable=True)
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)

    def to_json(self) -> str:
        return json.dumps(
            dict(
                uuid=str(self.uuid),
                name=self.name,
                occupation=self.occupation,
                company_email=self.company_email,
                credit_card_provider=self.credit_card_provider,
                phone_number=self.phone_number,
                date_of_birth=self.date_of_birth,
                city=self.city,
                tz=self.tz,
                latitude=self.latitude,
                longitude=self.longitude
            )
        )

    @staticmethod
    def geo_query(latitude: float, longitude: float, radius: int, unit: str = "km", limit: int = 100) -> list[dict]:

        if unit == "km":
            radius *= 1000

        elif unit != "mt":
            raise Exception(f"Unity {unit} not supported: use km | mt")

        query = f"""
            select profiles_distance.* from (
                SELECT p.*,
                    CAST(ST_DISTANCESPHERE(
                        ST_MAKEPOINT({latitude}, {longitude}), 
                        ST_MAKEPOINT(p.latitude, p.longitude)
                        ) AS INTEGER) AS distance
                FROM profile AS p
                order by distance 
                limit {limit}
            ) as profiles_distance
            where profiles_distance.distance <= {radius} 
        """

        with engine.connect() as con:
            result = con.execute(query)
            return list(map(lambda row: dict(row), result.fetchall()))
