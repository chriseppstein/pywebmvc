LIB_INSTALL_DIR=/tmp/addressBook/lib
RESOURCE_INSTALL_DIR=/tmp/addressBook/resources
APACHE_CONF_DIR=/etc/httpd/conf.d
TOP_DIR=/tmp/addressBook

deploy: install
	sudo apachectl restart

install: 
	sudo cp conf/addressBook_apache.conf ${APACHE_CONF_DIR}
	mkdir -p ${LIB_INSTALL_DIR}
	(cd src/code; find -name "*.py" | xargs tar -cf - | tar xf - -C ${LIB_INSTALL_DIR})
	mkdir -p ${RESOURCE_INSTALL_DIR}
	cp -f src/resources/{config.xml,MessageResources.properties} ${RESOURCE_INSTALL_DIR}
	(cd src/web && tar cf - * | tar xf - -C ${TOP_DIR})
