FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /service
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home appuser
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser gunicorn.conf.py ./
USER appuser
EXPOSE 8000
CMD ["gunicorn", "app:app"]
