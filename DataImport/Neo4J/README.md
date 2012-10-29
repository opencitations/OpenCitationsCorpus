# Neo4j database construction

This script reads metadata and references from the '../DATA'
directory and stores them in a neo4j graph database.


## Install guide:

If you don't have neo4j already installed on your system try the following:

*   sudo apt-get install python-jpype
*   git clone https://github.com/neo4j/python-embedded.git 
*   sudo python setup.py install
*   edit .bash.rc:   
    export CLASSPATH=/usr/lib/jvm/java-6-openjdk/jre/lib/
    export JAVA_HOME=/usr/lib/jvm/java-6-openjdk/jre/


## DB Structure diagram:
                           
>    PAPER <---[type]------ P1  <--[ref]-->  P2 
>                            |               |
>                            |[author]       |[author]
>                            v               v
>    AUTHOR <--[type]------ A1              A2

## Description:

*   Paper nodes, with properties:
    *   title
    *   abstract
    *   date         (YYYY-MM-DD, or YYYY, YYYY-MM  if data not available)
    *   source_url   (e.g. 'http://arxiv.org/abs/1001.1032' )
    *   source_id    (e.g. 'arxiv:1001.1032')
    *   unknown_references
    *   arxiv_meta_dict
        as a list of unicode strings (see remark below):
        > [ k1, v1 , k2, v2, ... ]
        vi are lists of meta_dict values joined with separator "|".
        An example dict is attached at the end of the file.

*   Reference relation: P1 ---> P2,  where P1,P2 are paper nodes. Properties:
    *   ref_string (e.g. 'Knuth, D., A remark on ... ')

*   Author nodes, with properties:
    *   name       (e.g. 'Knuth, Daniel-William')

*   Author relation: P ---> A, 
    where P in (Paper nodes) and A in (Author nodes)

*   Meta nodes: 
    - PAPER
    - AUTHOR

## Paradigm:

*   Keep the relation structure simple: Do not include relations, that can be 
    conveniently covered by an index/lookup table. How would we use this 
    traversal? It is always easy to add relations later on.
*   Do not throw away information.

## Install guide:

*   sudo apt-get install python-jpype
*   git clone https://github.com/neo4j/python-embedded.git 
*   sudo python setup.py install
*   edit .bash.rc:   
    > export CLASSPATH=/usr/lib/jvm/java-6-openjdk/jre/lib/
    > export JAVA_HOME=/usr/lib/jvm/java-6-openjdk/jre/

## Remark:

*   We use the embeded-python neo4j library. 
    As it turns out there are severe speed issues! 
    [https://github.com/neo4j/python-embedded/issues/15!](github/neo4j)
*   Propertis of Nodes and Relations can be:
    strings (unicode/ascii), integers, bools
    and lists of such. Dictionaries are not supported.

## References:
*   [Neo4J docs](http://docs.neo4j.org/chunked/milestone/python-embedded.html)
*   [Github repositoty](https://github.com/neo4j/python-embedded)
 
## Open Questions:

*   How to deal with unmatched references? 
    1.  Store them in paper_nodes?
           a. Store all references in paper_nodes 
              (redundant, since we want ref relation)
           b. Store matched references in relations 
              and unmatched ones in paper_node      
              (approach taken. Drawback: not very coherent)
    2.   Store them in a relation to a 'unknown_paper' node. (slow?!)
    3.   Add a new paper_node and a relation. (slow? data overload?)
