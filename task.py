import os
from app_config import redis_conn, session, logger, celery_app
from celery.schedules import crontab
from models import ProfileModel

@celery_app.task()
def build_redis_cache():

    if os.getenv("CLEAR_GEO_REDIS_BEFORE_INSERT", "1") == "1":
        redis_conn.delete(os.getenv("REDIS_GEOCACHE_NAME"))

    logger.info(f"Fazendo query")
    profiles = session.query(ProfileModel).all()

    logger.info(f"Copiando dados para o REDIS")
    for profile in profiles:
        redis_conn.geoadd(
            os.getenv("REDIS_GEOCACHE_NAME"),
            float(profile.longitude),
            float(profile.latitude),
            profile.to_json()
        )

    logger.info(f"Foram adicionados {len(profiles)}")


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Mantem o redis atualizado com novos registros do profile
    Aprimeira execução é quando o sistema incializa, as demais a cada 5 minutos
    """
    build_redis_cache.delay()
    sender.add_periodic_task(crontab(minute="*/5"), build_redis_cache.s())


if __name__ == "__main__":
    build_redis_cache()