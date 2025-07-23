#!/bin/bash -e
LOG_FILE=/tmp/codedeploy_scripts.log
exec > >(tee -a ${LOG_FILE} )
exec 2> >(tee -a ${LOG_FILE} >&2)
echo Script: after_install
echo `whoami`
echo `ls -ltra /home/ec2-user`
rm -rf /home/ec2-user/api
rm -rf /home/ec2-user/gardener-service-api
rm -rf /home/ec2-user/scripts
echo `ls -ltra /home/ec2-user`
echo `pwd`
cd /home/ec2-user
echo `pwd`
unzip -o /home/ec2-user/gardener-service-api.zip
echo `ls -ltra /home/ec2-user`