#!/bin/bash -e
LOG_FILE=/tmp/codedeploy_scripts.log
exec > >(tee -a ${LOG_FILE} )
exec 2> >(tee -a ${LOG_FILE} >&2)
echo Script: validate_service
echo `whoami`
echo `ls -ltra /var/run`
echo `ps -eaf | grep java`