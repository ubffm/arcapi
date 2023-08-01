FROM ubuntu:20.04

# install deps
RUN apt-get update && \
    apt-get install --no-install-recommends -y openjdk-16-jre-headless wget

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
ENV SOLR_VERSION=8.11.2
RUN ./download-solr.sh $SOLR_VERSION && \
    ./configure_cores.sh $SOLR_VERSION nlibooks nliauth

CMD ["solr-8.11.2/bin/solr", "start", "-f"]
