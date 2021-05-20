# -*- coding: utf8 -*-

"""
Special action to recompress all data
"""

__author__ = 'sergey'

import sys
from multiprocessing import cpu_count

def do_recompress(options, _fuse):
    """
    @param options: Commandline options
    @type  options: object

    @param _fuse: FUSE wrapper
    @type  _fuse: dedupsqlfs.fuse.dedupfs.DedupFS
    """

    isVerbosity = _fuse.getOption("verbosity") > 0

    tableHash = _fuse.operations.getTable("hash")
    tableHashCT = _fuse.operations.getTable("hash_compression_type")
    tableBlock = _fuse.operations.getTable("block")
    tableSubvol = _fuse.operations.getTable("subvolume")

    hashCount = tableHash.get_count()
    if isVerbosity:
        print("Ready to recompress %s blocks." % hashCount)

    cur = tableHash.getCursor(True)
    cur.execute("SELECT `id` FROM `%s`" % tableHash.getName())

    _fuse.operations.getManager().setAutocommit(False)
    tableBlock.begin()
    tableHashCT.begin()
    _fuse.operations.getManager().setAutocommit(True)

    # Every 100*100 (4x symbols)
    cntNth = int(hashCount/10000.0)
    if cntNth < 1:
        cntNth = 1

    # Process Nth blocks and then - commit
    maxCmmt = 5000
    cnt = cntNext = upd = cmmt = 0
    cpu_n = cpu_count() * 4

    try:
        toCompress = {}
        toCompressM = {}
        for hashItem in iter(cur.fetchone, None):

            cnt += 1
            cmmt += 1

            hashId = hashItem["id"]

            blockItem = tableBlock.get(hashId)
            hashCT = tableHashCT.get(hashId)
            curMethod = _fuse.operations.getCompressionTypeName(hashCT["type_id"])
            blockData = _fuse.decompressData(curMethod, blockItem["data"])

            toCompress[ hashId ] = blockData
            toCompressM[ hashId ] = curMethod

            if cnt % cpu_n == 0:

                for hashId, item in _fuse.compressData(toCompress):

                    cData, cMethod = item
                    curMethod = toCompressM[ hashId ]

                    if cMethod != curMethod:
                        cMethodId = _fuse.operations.getCompressionTypeId(cMethod)
                        res = tableBlock.update(hashId, cData)
                        res2 = tableHashCT.update(hashId, cMethodId)
                        if res and res2:
                            upd += 1

                toCompress = {}
                toCompressM = {}

            if cmmt >= maxCmmt:
                cmmt = 0
                _fuse.operations.getManager().setAutocommit(False)
                tableBlock.commit()
                tableHashCT.commit()
                tableBlock.begin()
                tableHashCT.begin()
                _fuse.operations.getManager().setAutocommit(True)

            if isVerbosity > 0:
                if cnt >= cntNext:
                    cntNext += cntNth
                    prc = "%6.2f%%" % (cnt*100.0/hashCount)
                    sys.stdout.write("\r%s " % prc)
                    sys.stdout.flush()

        if len(toCompress.keys()):
            for hashId, item in _fuse.compressData(toCompress):

                cData, cMethod = item
                curMethod = toCompressM[hashId]

                if cMethod != curMethod:
                    cMethodId = _fuse.operations.getCompressionTypeId(cMethod)
                    res = tableBlock.update(hashId, cData)
                    res2 = tableHashCT.update(hashId, cMethodId)
                    if res and res2:
                        upd += 1

    except:
        pass

    if isVerbosity:
        sys.stdout.write("\n")
        sys.stdout.flush()

    if isVerbosity:
        print("Processed %s blocks, recompressed %s blocks." % (cnt, upd,))

    if hashCount != cnt:
        _fuse.operations.getManager().setAutocommit(False)
        tableBlock.rollback()
        tableHashCT.rollback()
        _fuse.operations.getManager().setAutocommit(True)
        print("Something went wrong? Changes are rolled back!")
        return 1

    _fuse.operations.getManager().setAutocommit(False)
    tableBlock.commit()
    tableHashCT.commit()
    _fuse.operations.getManager().setAutocommit(True)

    subvCount = tableSubvol.get_count()

    if isVerbosity:
        print("Recalculate filesystem and %s subvolumes statistics." % subvCount)

    cur = tableSubvol.getCursor(True)
    cur.execute("SELECT * FROM `%s`" % tableSubvol.getName())

    _fuse.operations.getManager().setAutocommit(False)
    tableSubvol.begin()
    _fuse.operations.getManager().setAutocommit(True)

    from dedupsqlfs.fuse.subvolume import Subvolume

    sv = Subvolume(_fuse.operations)

    cnt = cntNext = 0
    cntNth = subvCount / 10000.0 / 3
    if cntNth < 1:
        cntNth = 1

    for subvItem in iter(cur.fetchone, None):

        sv.clean_stats(subvItem["name"])

        cnt += 1
        if cnt >= cntNext:
            cntNext += cntNth
            if isVerbosity:
                prc = "%6.2f%%" % (cnt * 100.0 / subvCount / 3)
                sys.stdout.write("\r%s " % prc)
                sys.stdout.flush()

        sv.get_usage(subvItem["name"], True)

        cnt += 1
        if cnt >= cntNext:
            cntNext += cntNth
            if isVerbosity:
                prc = "%6.2f%%" % (cnt * 100.0 / subvCount / 3)
                sys.stdout.write("\r%s " % prc)
                sys.stdout.flush()

        sv.get_root_diff(subvItem["name"])

        cnt += 1
        if cnt >= cntNext:
            cntNext += cntNth
            if isVerbosity:
                prc = "%6.2f%%" % (cnt * 100.0 / subvCount / 3)
                sys.stdout.write("\r%s " % prc)
                sys.stdout.flush()

    if isVerbosity:
        sys.stdout.write("\n")
        sys.stdout.flush()

    _fuse.operations.getManager().setAutocommit(False)
    tableSubvol.commit()
    _fuse.operations.getManager().setAutocommit(True)

    return 0
