# -*- coding: utf8 -*-

__author__ = 'sergey'

import os
import shutil

class DbManager( object ):

    _table = None
    _db_name = "dedupsqlfs"
    _base_path = "/dev/shm/db"
    _autocommit = True
    _synchronous = True

    _log = None

    tables = (
        "option",
        "tree",
        "name",
        "name_pattern_option",
        "inode",
        "inode_option",
        "link",
        "block",
        "xattr",
        "compression_type",
        "hash",
        "hash_compression_type",
        "inode_hash_block",
        "subvolume",
    )

    def __init__( self, dbname = None, base_path=None, autocommit=None, synchronous=None ):
        if not (dbname is None):
            self._db_name = dbname
        if not (base_path is None):
            self._base_path = dbname
        if not (autocommit is None):
            self._autocommit = autocommit == True
        if not (synchronous is None):
            self._synchronous = synchronous == True
        self._table = {}
        pass

    def setLogger(self, logger):
        self._log = logger
        return self

    def getLogger(self):
        return self._log

    def setSynchronous(self, flag=True):
        self._synchronous = flag == True
        return self

    def getSynchronous(self):
        return self._synchronous

    def setAutocommit(self, flag=True):
        self._autocommit = flag == True
        return self

    def getAutocommit(self):
        return self._autocommit

    def setTableEngine(self, engine):
        return self

    def getTableEngine(self):
        return self

    def setBasepath(self, base_path):
        self._base_path = base_path
        return self

    def getBasePath(self):
        return self._base_path

    def getDbName(self):
        return self._db_name

    def getTable(self, name, nocreate=False):
        if name not in self._table:
            if name == "option":
                from dedupsqlfs.db.sqlite.table.option import TableOption
                self._table[ name ] = TableOption(self)
            elif name == "tree":
                from dedupsqlfs.db.sqlite.table.tree import TableTree
                self._table[ name ] = TableTree(self)
            elif name.startswith("tree_"):
                from dedupsqlfs.db.sqlite.table.tree import TableTree
                self._table[ name ] = TableTree(self)
                self._table[ name ].setName(name)
            elif name == "name":
                from dedupsqlfs.db.sqlite.table.name import TableName
                self._table[ name ] = TableName(self)
            elif name == "inode":
                from dedupsqlfs.db.sqlite.table.inode import TableInode
                self._table[ name ] = TableInode(self)
            elif name.startswith("inode_") \
                    and not name.startswith("inode_hash_block") \
                    and not name.startswith("inode_option"):
                from dedupsqlfs.db.sqlite.table.inode import TableInode
                self._table[ name ] = TableInode(self)
                self._table[ name ].setName(name)
            elif name == "link":
                from dedupsqlfs.db.sqlite.table.link import TableLink
                self._table[ name ] = TableLink(self)
            elif name.startswith("link_"):
                from dedupsqlfs.db.sqlite.table.link import TableLink
                self._table[ name ] = TableLink(self)
                self._table[ name ].setName(name)
            elif name == "block":
                from dedupsqlfs.db.sqlite.table.block import TableBlock
                self._table[ name ] = TableBlock(self)
            elif name == "xattr":
                from dedupsqlfs.db.sqlite.table.xattr import TableInodeXattr
                self._table[ name ] = TableInodeXattr(self)
            elif name.startswith("xattr_"):
                from dedupsqlfs.db.sqlite.table.xattr import TableInodeXattr
                self._table[ name ] = TableInodeXattr(self)
                self._table[ name ].setName(name)
            elif name == "compression_type":
                from dedupsqlfs.db.sqlite.table.compression_type import TableCompressionType
                self._table[ name ] = TableCompressionType(self)
            elif name == "hash_compression_type":
                from dedupsqlfs.db.sqlite.table.hash_compression_type import TableHashCompressionType
                self._table[ name ] = TableHashCompressionType(self)
            elif name == "hash_sizes":
                from dedupsqlfs.db.sqlite.table.hash_sizes import TableHashSizes
                self._table[ name ] = TableHashSizes(self)
            elif name == "name_pattern_option":
                from dedupsqlfs.db.sqlite.table.name_pattern_option import TableNamePatternOption
                self._table[ name ] = TableNamePatternOption(self)
            elif name == "inode_option":
                from dedupsqlfs.db.sqlite.table.inode_option import TableInodeOption
                self._table[ name ] = TableInodeOption(self)
            elif name.startswith("inode_option_"):
                from dedupsqlfs.db.sqlite.table.inode_option import TableInodeOption
                self._table[ name ] = TableInodeOption(self)
                self._table[ name ].setName(name)
            elif name == "hash":
                from dedupsqlfs.db.sqlite.table.hash import TableHash
                self._table[ name ] = TableHash(self)
            elif name == "inode_hash_block":
                from dedupsqlfs.db.sqlite.table.inode_hash_block import TableInodeHashBlock
                self._table[ name ] = TableInodeHashBlock(self)
            elif name.startswith("inode_hash_block_"):
                from dedupsqlfs.db.sqlite.table.inode_hash_block import TableInodeHashBlock
                self._table[ name ] = TableInodeHashBlock(self)
                self._table[ name ].setName(name)
            elif name == "subvolume":
                from dedupsqlfs.db.sqlite.table.subvolume import TableSubvolume
                self._table[ name ] = TableSubvolume(self)
            elif name == "tmp_ids":
                from dedupsqlfs.db.sqlite.table.tmp_ids import TableTmpIds
                self._table[ name ] = TableTmpIds(self)
            elif name == "tmp_id_count":
                from dedupsqlfs.db.sqlite.table.tmp_id_count import TableTmpIdCount
                self._table[ name ] = TableTmpIdCount(self)
            else:
                raise ValueError("Unknown database %r" % name)

            if not nocreate:
                self._table[ name ].create()

        return self._table[ name ]


    def begin(self):
        for name, t in self._table.items():
            t.begin()
        return self

    def commit(self):
        for name, t in self._table.items():
            t.commit()
        return self

    def rollback(self):
        for name, t in self._table.items():
            t.rollback()
        return self

    def vacuum(self):
        for name, t in self._table.items():
            t.vacuum()
        return self

    def close(self):
        for name, t in self._table.items():
            t.close()
        return self

    def getSize(self):
        s = 0
        for name, t in self._table.items():
            s += t.getSize()
        return s

    def isSupportedStorage(self):
        s = False
        for name in self.tables:
            t = self.getTable(name, True)
            f = t.getDbFilePath()
            if os.path.isfile(f):
                s = True
        return s

    def getFileSize(self):
        s = 0
        for name in self.tables:
            t = self.getTable(name, True)
            s += t.getFileSize()
        return s

    def getOperationsCount(self):
        s = 0
        for name in self.tables:
            t = self.getTable(name, True)
            s += t.getAllOperationsCount()
        return s

    def getTimeSpent(self):
        s = 0
        for name in self.tables:
            t = self.getTable(name, True)
            s += t.getAllTimeSpent()
        return s

    def create(self):
        #for t in self.tables:
        #    self.getTable(t).create()
        return self

    def copy(self, oldTableName, newTableName):
        t1 = self.getTable(oldTableName, True)
        t2 = self.getTable(newTableName, True)

        t1.create()
        t1.close()

        # Rename files
        shutil.copyfile(t1.getDbFilePath(), t2.getDbFilePath())
        t2.getCursor().execute("ALTER TABLE `%s` RENAME TO `%s`" % (oldTableName, newTableName,))
        return self

    pass
