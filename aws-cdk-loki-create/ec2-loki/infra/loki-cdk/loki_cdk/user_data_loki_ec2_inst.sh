#!/bin/bash

########## UserData exclusively for Grafana Loki EC2 Instance #########

### update yum ###
sudo yum update -y

### Install Grafana 10.4 stable release 03/2024 ###
sudo yum install -y https://dl.grafana.com/oss/release/grafana-10.4.1-1.x86_64.rpm
sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl enable grafana-server.service

### Install docker for EC2 Instance for Loki ###
sudo amazon-linux-extras install -y docker
sudo systemctl start docker
sudo systemctl enable docker

### Install docker-compose for Loki ###
sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
# docker-compose version     ## output this to a file.

### Install Loki - Docker version ###
mkdir -p /srv/loki
cd /srv/loki || exit 1

wget https://raw.githubusercontent.com/grafana/loki/v2.9.4/cmd/loki/loki-local-config.yaml -O loki-config.yaml
## Replace loki-config.yaml with loki-s3-storage-config.yaml
sudo docker run --name loki -d -v $(pwd):/mnt/config -p 3100:3100 grafana/loki:2.9.4 -config.file=/mnt/config/loki-config.yaml

cd -

### NOTE: Loki running as docker works but below is are steps for local option ###

### Install Loki ###
# wget https://github.com/grafana/loki/releases/download/v2.5.0/loki-linux-amd64.zip
# unzip loki-linux-amd64.zip
# sudo mv loki-linux-amd64/loki /usr/local/bin/
# sudo chmod +x /usr/local/bin/loki

### Following this configure Loki run under systemctl ###
