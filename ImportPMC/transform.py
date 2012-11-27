#!/usr/bin/env python

# Path to the Saxon and Apache XML Commons Resolver Java archives
#COMMONS_RESOLVER="/usr/share/java/saxon.jar:xml-commons-resolver-1.2/resolver.jar"
COMMONS_RESOLVER = "./saxon.jar:xml-commons-resolver-1.2/resolver.jar"

xsl = "article-data.xsl"
input_directory = "data/"
output_directory = "out/"

from subprocess import call
import os

def transform(source,target):
    """
    Applies the xsl tranformation the source file and writes it to the target
    """
    
    args = ['java', 
            '-Xmx2048m', 
            '-cp', './saxon.jar:xml-commons-resolver-1.2/resolver.jar', 
            '-Dxml.catalog.files=catalog.xml', 
            'net.sf.saxon.Transform', 
            '-r:org.apache.xml.resolver.tools.CatalogResolver', 
            '-x:org.apache.xml.resolver.tools.ResolvingXMLReader', 
            '-y:org.apache.xml.resolver.tools.ResolvingXMLReader', 
            '-xsl:'+xsl, 
            '-s:' + source,
            '-o:' + target
            ]
    
    return call(args)
    

def main():
    """
    Applies xsl-tranform to all files in subdirectories of input_directory
    """

    if not os.path.exists(output_directory):
        print "Creating output directory"
        os.makedirs(output_directory)
    
    for dirpath, subsubdirs, filenames in os.walk(input_directory):
        for filename in filenames:
            if not filename.endswith('.nxml'): continue

            # remove first subdir (=input_directory) from dirpath and append output_dir
            new_dir = os.path.join(output_directory, "/".join(dirpath.split('/')[1:]))

            print "transforming", filename
            if transform(
                os.path.join(dirpath, filename),
                os.path.join(new_dir, filename + ".xml")
                ):
                print "Error transforming", filename


if __name__ == "__main__":
    main()
