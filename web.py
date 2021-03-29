import json
import os
from app_config import flask_app, redis_conn,session
from models import ProfileModel
from sqlalchemy import func


@flask_app.route('/')
def index():
    count = session.query(func.count(ProfileModel.id)).scalar()
    return f"""
        Database Registers: {count}  
        <a href='http://127.0.0.1:5000/georedis_profiles/33.7207/-116.21677/100/km'> REDIS REQUEST<a>
        <a href='http://127.0.0.1:5000/postgis_profiles/33.7207/-116.21677/100/km'> POSTGIS REQUEST<a>
    """

# http://127.0.0.1:5000/georedis_profiles/33.7207/-116.21677/100/km
@flask_app.route('/georedis_profiles/<latitude>/<longitude>/<int:radius>/<unit>/')
def georedis_profiles(latitude, longitude, radius, unit):

    results = redis_conn.georadius(
        os.getenv("REDIS_GEOCACHE_NAME"),
        float(longitude),
        float(latitude),
        radius,
        unit=unit
    )[0: 100]

    return dict(results=list(map(lambda x: json.loads(x.decode("utf-8")), results))), 200


# http://127.0.0.1:5000/postgis_profiles/33.7207/-116.21677/100/km
@flask_app.route('/postgis_profiles/<latitude>/<longitude>/<int:radius>/<unit>/')
def postgis_profiles(latitude, longitude, radius, unit):

    results = ProfileModel.geo_query(
        float(latitude),
        float(longitude),
        radius,
        unit,
        limit=100
    )

    return dict(results=results), 200
