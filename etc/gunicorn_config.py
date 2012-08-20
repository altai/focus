import multiprocessing

bind = "0.0.0.0:8080"

formula_workers_count = multiprocessing.cpu_count() * 2 + 1
if formula_workers_count < 4:
    workers = 4
elif formula_workers_count > 12:
    workers = 12
else:
    workers = formula_workers_count

timeout = 86400
accesslog = '/var/log/focus/gunicorn.access-log'
errorlog = '/var/log/focus/gunicorn.error-log'

logger_class = 'focus.glogging.Logger'
LOG_MAX_BYTES = 1024 * 1024 * 100
LOG_BACKUP_COUNT = 12
