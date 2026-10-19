FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home appuser
COPY --chown=appuser:appuser app.py database.py validation.py gunicorn.conf.py ./
COPY --chown=appuser:appuser templates ./templates
COPY --chown=appuser:appuser static ./static
USER appuser
EXPOSE 8000
CMD ["gunicorn", "app:app"]
