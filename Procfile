web: python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn socialnetwork.wsgi:application --bind 0.0.0.0:$PORT --workers 2
