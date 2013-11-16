
import sys
import os

dirname = "dedupsqlfs"

# Figure out the directy which is the prefix
# path-of-current-file/..
curpath = os.path.abspath( sys.argv[0] )
if os.path.islink(curpath):
    curpath = os.readlink(curpath)
currentdir = os.path.dirname( curpath )
basedir = os.path.abspath( os.path.join( currentdir, ".." ) )

sys.path.insert( 0, basedir )

COMPRESSION_SUPPORTED=('lzo', 'zlib', 'bz2', 'lzma', 'snappy', 'lz4',)

CLENGTHS={}

for l in range(1, 256, 1):
    print("Length: %d" % l)

    done = True

    for c in COMPRESSION_SUPPORTED:
        m = __import__(c)

        if not c in CLENGTHS:
            CLENGTHS[ c ] = {
                "done" : False
            }

        if CLENGTHS[ c ]["done"]:
            continue
        else:
            done = False

        CLENGTHS[ c ]["length"] = l

        s = b'a' * l
        cs = m.compress(s)
        if len(s) > len(cs):
            CLENGTHS[ c ]["done"] = True


    if done:
        break

for c in CLENGTHS:
    print("method: %r, min length: %r" % (c, CLENGTHS[c]["length"]))
