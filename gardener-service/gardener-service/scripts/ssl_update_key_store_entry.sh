#!/bin/bash -e

CERT_PATH=/opt/gardener/cert/
CERT_ALIAS=farmlab_wildcard_acm_cert
PKCS_FILENAME=pkcs.p12
PKCS_PW='my_pkcs_pw'
KEYSTORE_FILENAME=keystore.jks
KEYSTORE_PW='my_keystore_pw'
GARDENER_CERT_ACM_ARN=arn:aws:acm:us-west-2:123456789012:certificate/ee027dc3-6a5a-40e9-9337-624cdc99d3fb

# create the directory CERT_PATH if needed
mkdir -p $CERT_PATH

# download *.farmlab.asnyder.com CERT from ACM if not present using awscli
# *.farmlab.asnyder.com CERT = arn:aws:acm:us-west-2:123456789012:certificate/ee027dc3-6a5a-40e9-9337-624cdc99d3fb
cd $CERT_PATH
aws acm get-certificate --region us-west-2 --certificate-arn $GARDENER_CERT_ACM_ARN

# NOTE: To download it might need to do the following instead.
sudo sh -c 'sudo aws acm get-certificate --region us-west-2 --certificate-arn $GARDENER_CERT_ACM_ARN > cert.txt'
# NOTE: Might need to code here to parse out CERT.


# generate PKCS12 file
openssl pkcs12 -export -in $CERT_PATH/fullchain.pem -inkey $CERT_PATH/privkey.pem -out $PKCS_FILENAME -name $CERT_ALIAS -passout pass:$PKCS_PW

# delete existing entry in Java keystore
keytool -delete -keystore $KEYSTORE_FILENAME -alias $CERT_ALIAS -storepass $KEYSTORE_PW

# add new Java keystore entry from PKCS12 file
keytool -importkeystore -deststorepass $KEYSTORE_PW -destkeypass $KEYSTORE_PW -destkeystore $KEYSTORE_FILENAME -srckeystore $PKCS_FILENAME -srcstoretype PKCS12 -srcstorepass $PKCS_PW -alias $CERT_ALIAS

rm $PKCS_FILENAME