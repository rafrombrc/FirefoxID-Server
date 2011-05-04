#! /bin/bash
if [ "~whoami`" != 'root' ]
then echo "Please run this command as Root"
exit
fi
INSTALL = apt-get install
echo "#### Installing extra libraries "
$INSTALL python-2.6
$INSTALL python-virtualenv
$INSTALL libsasl2-dev
$INSTALL python-cxx-dev
$INSTALL libldap2-dev
$INSTALL nginx
echo "#### Adding HTML directories "
mkdir -p /var/www
ln -s /var/www/sample sample
ln -s var/www/s static
echo "#### Copying nginx config files."
cp /etc/nginx/nginx.conf{,.backup-`date +'%Y%m%d'`}
cp conf/nginx/nginx.conf.UBUNTU /etc/nginx/nginx.conf
cp conf/nginx/conf.d/* /etc/nginx/conf.d/*
ln -s /etc/nginx/conf.d /etc/nginx/conf.d/ssl
echo "#### Making self-signed certs (You\'ll have to do things now)."
pushd certs
bash make_ss_certs.sh
popd
echo "#### Restarting nginx"
/etc/init,d/nginx restart
echo "####"
echo " With any hope, you now have a properly configured stand alone identity server.

You should be able to go to http://localhost/1/login and see the login page.
"
