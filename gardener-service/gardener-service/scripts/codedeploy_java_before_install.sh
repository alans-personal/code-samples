#!/bin/bash -e
LOG_FILE=/tmp/codedeploy_scripts.log
exec > >(tee -a ${LOG_FILE} )
exec 2> >(tee -a ${LOG_FILE} >&2)
echo Script: before_install
echo `whoami`
echo `pwd`
echo `ls`
echo Checking: SSL CERT directory
echo `mkdir -p /opt/gardener/cert`
echo `ls -ltra /opt/gardener/cert`
echo Download CERT when not found

echo NOTE: Currently Downloading CERT is manual process
echo NOTE: Needed once each when a new EC2 Instance is spun up
echo NOTE: This can be automated by checking and calling a
echo NOTE: ssl_update_key_store_entry.sh when CERT is not present

echo Checking: home directory
echo `ls -ltra /home/ec2-user`
rm -f /home/ec2-user/gardener-service-api.zip
rm -f /home/ec2-user/log4j2.xml
echo `ls -ltra /home/ec2-user`
echo Checking: Gardener service status
echo `ps -eaf | grep java`
echo `sudo service gardener status`