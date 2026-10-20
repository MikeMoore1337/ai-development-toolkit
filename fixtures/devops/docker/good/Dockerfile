# Synthetic Dockerfile. Not built in the Toolkit CI.
FROM python:3.12-slim
WORKDIR /srv
COPY --chown=10001:10001 app.py /srv/app.py
USER 10001
EXPOSE 8080
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)"
CMD ["python", "/srv/app.py"]
