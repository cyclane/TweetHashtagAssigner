FROM python:3.7.8

RUN apt update && \
    apt install git && \
    pip install flask && \
    git clone https://github.com/Gleb-ko/TweetHashtagAssigner.git /app


WORKDIR /app
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 80
CMD ["sh", "start.sh"]