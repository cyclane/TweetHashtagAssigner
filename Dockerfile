FROM tiangolo/uwsgi-nginx-flask:latest

ENV STATIC_PATH /app/website
ENV STATIC_INDEX 1

WORKDIR /

RUN apt update && \
    apt upgrade -y && \
    apt install ca-certificates -y && \
    rm -rf /app && \
    git clone https://github.com/Gleb-ko/TweetHashtagAssigner.git /app

WORKDIR /app
CMD ["sh", "start.sh"]