FROM python:3.6-slim-stretch

ARG APP_DIR
WORKDIR $APP_DIR
ENV PYTHONPATH=$APP_DIR:$PYTHONPATH

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "play_drums.py"]
