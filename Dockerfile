FROM ghcr.io/some_private_user/tiktok-utils:dev

ENV PATH "/app/scripts:${PATH}"
ENV PYTHONPATH "${PYTHONPATH}:/app"

ARG APP_PORT=8080

EXPOSE ${APP_PORT}

# Set the working directory
WORKDIR /app

COPY requirements*  /app/
RUN apt-get -y update
RUN python3.8 -m pip install -r requirements.txt
ADD . /app/


RUN ["chmod", "+x", "/app/scripts/docker-entrypoint.sh"]


ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]

CMD ["run-production"]
