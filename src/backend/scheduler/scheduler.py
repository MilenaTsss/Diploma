import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore

_scheduler = None
logger = logging.getLogger(__name__)


def get_scheduler():
    global _scheduler

    if _scheduler is None:
        logger.info("Creating new scheduler instance")
        _scheduler = BackgroundScheduler()
        _scheduler.add_jobstore(DjangoJobStore(), alias="default")

    if not _scheduler.running:
        logger.info("Starting scheduler instance")
        _scheduler.start()

    return _scheduler
