FROM ubuntu:20.04 as build
# install deps
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        python3-pip python3.8-venv python3-dev hspell git gcc

# set up app user
RUN mkdir -p /home/app
RUN groupadd -r app &&\
    useradd -r -g app -d /home/app -s /sbin/nologin -c "Docker image user" app

ENV HOME=/home/app
ENV APP_HOME=/home/app/project-dir

RUN mkdir $APP_HOME
WORKDIR $APP_HOME

ADD . $APP_HOME
RUN chown -R app:app $HOME

USER app

# download and configure arc
RUN ./project_setup.sh


FROM ubuntu:20.04
# install deps
RUN apt-get update && \
    apt-get install --no-install-recommends -y hspell python3

# set up app user
RUN mkdir -p /home/app
RUN groupadd -r app &&\
    useradd -r -g app -d /home/app -s /sbin/nologin -c "Docker image user" app

ENV HOME=/home/app
ENV APP_HOME=/home/app/project-dir

COPY --from=build /home/app /home/app
RUN chown -R app:app $HOME
WORKDIR $APP_HOME

USER app

CMD ["./run_arcapi.sh"]
