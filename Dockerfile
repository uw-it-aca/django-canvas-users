FROM acait/django-container:1.1.8 as app-container

USER root
RUN apt-get update && apt-get install mysql-client libmysqlclient-dev -y
USER acait

ADD --chown=acait:acait canvas_users/VERSION /app/canvas_users/
ADD --chown=acait:acait setup.py /app/
ADD --chown=acait:acait requirements.txt /app/

RUN . /app/bin/activate && pip install -r requirements.txt
RUN . /app/bin/activate && pip install mysqlclient

ADD --chown=acait:acait . /app/
ADD --chown=acait:acait docker/ project/

RUN . /app/bin/activate && pip install nodeenv && nodeenv -p &&\
    npm install -g npm && ./bin/npm install -g less

RUN . /app/bin/activate && python manage.py collectstatic --noinput

FROM acait/django-test-container:1.1.8 as app-test-container

COPY --from=app-container /app/ /app/
COPY --from=app-container /static/ /static/
