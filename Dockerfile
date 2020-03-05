FROM       ubuntu:16.04
MAINTAINER wnaldj1589@twinny.co.kr

ARG ssh_pub_key
ARG ssh_prv_key

RUN apt-get update -qq -y

RUN apt-get install -qq -y python3 python3-pip apache2 git doxygen graphviz

RUN mkdir -p /work/doxygen/repos && \
    mkdir -p /work/www && \
    mkdir -p /work/doxygen/conf

ENV WORK_DIR "/work/doxygen/"
ENV WWW_DIR "/work/www/"
ENV LOG_DIR "/work/log/"
ENV GIT_TARGET ""

WORKDIR ${WORK_DIR}

COPY conf/* ${WORK_DIR}/conf/

RUN mkdir -p /root/.ssh/ && \
    chmod 0700 /root/.ssh && \
    ssh-keyscan github.com > /root/.ssh/known_hosts

RUN echo "$ssh_pub_key" > /root/.ssh/id_rsa.pub && \
    echo "$ssh_prv_key" > /root/.ssh/id_rsa && \
    chmod 0700 /root/.ssh/*

RUN cp ${WORK_DIR}/conf/apache2.conf /etc/apache2/ && \
    cp ${WORK_DIR}/conf/ports.conf /etc/apache2/ && \
    cp ${WORK_DIR}/conf/000-default.conf /etc/apache2/sites-available/

COPY requirements.txt ${WORK_DIR}

RUN pip3 install -qq -r requirements.txt

COPY Auth.json Doxyfile gitRepoMonitor.py start.sh ${WORK_DIR}

RUN mkdir ${LOG_DIR}

EXPOSE 8888
