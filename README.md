Open Street Map to Mongodb compiler
===================================

This is a framework to process OSM data dumps in PBF format.

There's an included backend to store data in mongodb, to implement a new backend it's very simple, just implement osm.sink which does an action on the processed entities and osm.factory which creates the instances of OSM entitities. Then call the parser with your implementations of sink and factory.


Boot
----
Initialize the submodules:

    git submodule init
    git submodule update

Dependencies:
------------
python-pymongo
python-protobuf

Usage:
------


<pre>
./osm_mongo_compiler.py spain.osm.pbf 
Loading: spain.osm.pbf
Counting blobs...  3829.
Bounding Box: (-9.779014,35.91539) (5.098525,44.14855)
[      0% 7/3829 blocks. 56 K nodes 2012-08-26 18:58      ]
</pre>


MapReduce
---------

Count the number of data blocks with:
./osm_mongo_compiler.py file --count yes

By running with -f and -n options the file can be devided in ranges and thus processing be done in a map kind of job across several processors or nodes.
./osm_mongo_compiler.py file -f 0 -n 1000
./osm_mongo_compiler.py file -f 1000 -n 1000
...
etc

Credits
-------
Feedback welcome to <pedro.larroy.lists@gmail.com> please put [osmcompiler] on the subject or your mails will be probably ignored.
Based initially on the parsepbf tool by Chris Hill.
