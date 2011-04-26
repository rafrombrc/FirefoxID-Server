! /bin/bash
name=ss_identity
echo ####
echo Generating $name.key 
openssl genrsa -des3 -out $name.key 4096
echo ####
echo Generating signing request
openssl req -new -key $name.key -out $name.csr
echo ####
echo Signing request for 365 days
openssl x509 -req -days 365 -in $name.csr -signkey $name.key -out $name.crt
echo ####
echo Stripping password from $name.key
openssl rsa -in $name.key -out $name.key.insecure
mv $name.key $name.key.secure
mv $name.key.insecure $name.key
echo ####
echo Creating cert directory
mkdir -p /var/certs
echo ####
echo Copying self-signed certs to cert directory
cp $name.key $name.crt /var/certs
echo ####
echo All Done.
echo ####

