#!/usr/bin/env bash

OTHER=""

if [ $3 ]; then
    OTHER="$OTHER -o:$3"
fi


# Path to the Saxon and Apache XML Commons Resolver Java archives
COMMONS_RESOLVER="/usr/share/java/saxon.jar:xml-commons-resolver-1.2/resolver.jar"

java -Xmx2048m \
     -cp $COMMONS_RESOLVER \
     -Dxml.catalog.files=catalog.xml net.sf.saxon.Transform \
     -r:org.apache.xml.resolver.tools.CatalogResolver \
     -x:org.apache.xml.resolver.tools.ResolvingXMLReader \
     -y:org.apache.xml.resolver.tools.ResolvingXMLReader \
     -xsl:$1 \
     -s:$2 \
     $OTHER
