#!/usr/bin/env bash
while true; do
    docker build --tag doxygen_monitor:0.1 --build-arg ssh_pub_key="$(cat ~/.ssh/id_rsa.pub)" --build-arg ssh_prv_key="$(cat ~/.ssh/id_rsa)" .
    docker run -it --rm -p9999:8888 --name doxygen -v $PWD/log:/work/log -v $PWD/repos:/work/doxygen/repos doxygen_monitor:0.1 ./start.sh 
done
