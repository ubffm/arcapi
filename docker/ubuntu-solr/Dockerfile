FROM ubuntu:22.04
ARG SOLR_URL
RUN echo $SOLR_URL

# install deps
RUN apt-get update && \
    apt-get install --no-install-recommends -y openjdk-19-jre-headless wget

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
RUN ./download-solr.sh $SOLR_URL && \
    ./configure_cores.sh nlibooks nliauth

CMD ["solr/bin/solr", "start", "-f"]
