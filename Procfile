# Procfile para Sistema de Actas Municipales de Pastaza
# Para uso con plataformas como Heroku o Railway

web: gunicorn config.wsgi:application --log-file -
worker: celery -A config worker -l info
beat: celery -A config beat -l info
flower: celery -A config flower --port=$PORT
