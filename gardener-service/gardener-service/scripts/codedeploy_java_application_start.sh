#!/bin/bash -e
LOG_FILE=/tmp/codedeploy_scripts.log
exec > >(tee -a ${LOG_FILE} )
exec 2> >(tee -a ${LOG_FILE} >&2)
echo Script: application_start
echo `whoami`
echo `sudo service gardener status`
echo `sudo service gardener restart`