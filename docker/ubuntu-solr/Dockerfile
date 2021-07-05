FROM ubuntu:latest

# install deps
RUN apt-get update && \
    apt-get install --no-install-recommends -y openjdk-14-jre-headless wget

# set up app user
RUN mkdir -p /home/app
RUN groupadd -r app &&\
    useradd -r -g app -d /home/app -s /sbin/nologin -c "Docker image user" app

ENV HOME=/home/app
ENV APP_HOME=/home/app/project-dir

RUN mkdir $APP_HOME
WORKDIR $APP_HOME

ADD . $APP_HOME
RUN chown -R app:app $APP_HOME

USER app

# download and configure solr
ENV SOLR_VERSION=8.8.1
RUN ./download-solr.sh $SOLR_VERSION && \
    ./configure_cores.sh $SOLR_VERSION nlibooks nliauth

CMD ["solr-8.8.1/bin/solr", "start", "-f"]
