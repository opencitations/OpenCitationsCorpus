#!/usr/bin/env bash

OTHER=""
if [ $2 ]; then
    OTHER="-o:$2"
fi

# Path to the Saxon and Apache XML Commons Resolver Java archives
COMMONS_RESOLVER="/usr/share/java/saxon.jar:/home/alex/src/xml-commons-resolver-1.2/resolver.jar"

java -cp $COMMONS_RESOLVER \
     -Dxml.catalog.files=catalog.xml net.sf.saxon.Transform \
     -r:org.apache.xml.resolver.tools.CatalogResolver \
     -x:org.apache.xml.resolver.tools.ResolvingXMLReader \
     -y:org.apache.xml.resolver.tools.ResolvingXMLReader \
     -xsl:article-graph.xsl \
     -s:$1 \
     $OTHER
