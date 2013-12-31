# -*- coding: utf8 -*-

__author__ = 'sergey'

import os
from time import sleep
import subprocess
import pymysql
import pymysql.err
import pymysql.cursors

cursor_type = pymysql.cursors.DictCursor

class DbManager( object ):

    _table = None
    _table_engine = 'MyISAM'
    _db_name = "dedupsqlfs"
    _base_path = "/dev/shm/db"
    _autocommit = True
    _synchronous = True

    _socket = None
    _notmeStarted = False
    _user = "root"
    _pass = ""

    _conn = None

    _mysqld_proc = None
    """
    @ivar _mysqld_proc:
    @type _mysqld_proc: L{subprocess.Popen}
    """

    _buffer_size = 512*1024*1024
    """
    @ivar _buffer_size: InnoDB pool buffer size
    """

    tables = (
        "option",
        "tree",
        "name",
        "inode",
        "link",
        "block",
        "xattr",
        "compression_type",
        "hash",
        "hash_compression_type",
        "hash_block_size",
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
        if not engine:
            engine = 'MyISAM'
        self._table_engine = engine
        return self

    def getTableEngine(self):
        return self._table_engine

    def setBasepath(self, base_path):
        self._base_path = base_path
        return self

    def setBufferSize(self, in_bytes):
        self._buffer_size = in_bytes
        return self

    def getBasePath(self):
        return self._base_path

    def getDbName(self):
        return self._db_name

    def getSocket(self):
        return self._socket

    def getUser(self):
        return self._user

    def getPassword(self):
        return self._pass


    def getTable(self, name):
        if name not in self._table:
            if name == "option":
                from dedupsqlfs.db.mysql.table.option import TableOption
                self._table[ name ] = TableOption(self)
            elif name == "tree":
                from dedupsqlfs.db.mysql.table.tree import TableTree
                self._table[ name ] = TableTree(self)
            elif name == "name":
                from dedupsqlfs.db.mysql.table.name import TableName
                self._table[ name ] = TableName(self)
            elif name == "inode":
                from dedupsqlfs.db.mysql.table.inode import TableInode
                self._table[ name ] = TableInode(self)
            elif name == "link":
                from dedupsqlfs.db.mysql.table.link import TableLink
                self._table[ name ] = TableLink(self)
            elif name == "block":
                from dedupsqlfs.db.mysql.table.block import TableBlock
                self._table[ name ] = TableBlock(self)
            elif name == "xattr":
                from dedupsqlfs.db.mysql.table.xattr import TableInodeXattr
                self._table[ name ] = TableInodeXattr(self)
            elif name == "compression_type":
                from dedupsqlfs.db.mysql.table.compression_type import TableCompressionType
                self._table[ name ] = TableCompressionType(self)
            elif name == "hash_compression_type":
                from dedupsqlfs.db.mysql.table.hash_compression_type import TableHashCompressionType
                self._table[ name ] = TableHashCompressionType(self)
            elif name == "hash_block_size":
                from dedupsqlfs.db.mysql.table.hash_block_size import TableHashBlockSize
                self._table[ name ] = TableHashBlockSize(self)
            elif name == "hash":
                from dedupsqlfs.db.mysql.table.hash import TableHash
                self._table[ name ] = TableHash(self)
            elif name == "inode_hash_block":
                from dedupsqlfs.db.mysql.table.inode_hash_block import TableInodeHashBlock
                self._table[ name ] = TableInodeHashBlock(self)
            elif name == "subvolume":
                from dedupsqlfs.db.mysql.table.subvolume import TableSubvolume
                self._table[ name ] = TableSubvolume(self)
            else:
                raise ValueError("Unknown database %r" % name)
        return self._table[ name ]


    def isSupportedStorage(self):
        s = False
        datadir = self.getBasePath() + "/mysql-db-data"
        if os.path.isdir(datadir):
            s = True
        return s


    def startMysqld(self):
        if self._mysqld_proc is None:

            logfile = self.getBasePath() + "/error.log"
            slowlogfile = self.getBasePath() + "/slow.log"
            pidfile = self.getBasePath() + "/mysql.pid"
            self._socket = self.getBasePath() + "/mysql.sock"

            if os.path.exists(self._socket):
                self._notmeStarted = True
                return True

            tmpdir = self.getBasePath() + "/tmp"
            if not os.path.isdir(tmpdir):
                os.makedirs(tmpdir, 0o0750)

            is_new = False
            datadir = self.getBasePath() + "/mysql-db-data"
            if not os.path.isdir(datadir):
                is_new = True
                os.makedirs(datadir, 0o0750)

            is_mariadb = False
            output = subprocess.check_output(["mysqld", "--version"])
            if output.find(b'MariaDB'):
                is_mariadb = True

            cmd_opts = [
                "--basedir=/usr",
                "--datadir=%s" % datadir,
                "--tmpdir=%s" % tmpdir,
                "--plugin-dir=/var/lib/mysql/plugin",
                "--log-error=%s" % logfile,
                "--slow-query-log",
                "--slow-query-log-file=%s" % slowlogfile,
                "--pid-file=%s" % pidfile,
                "--skip-grant-tables",
                "--skip-bind-address",
                "--skip-networking",
                "--skip-name-resolve",
                "--socket=%s" % self.getSocket(),
                "--default-storage-engine=InnoDB",
                # TODO: options
                "--connect-timeout=10",
                "--interactive-timeout=3600",
                "--wait-timeout=3600",
            ]
            if self.getAutocommit():
                cmd_opts.append("--autocommit")
            else:
                cmd_opts.append("--skip-autocommit")

            if self.getSynchronous():
                cmd_opts.append("--flush")
                cmd_opts.append("--innodb-flush-log-at-trx-commit=1")
            else:
                cmd_opts.append("--innodb-flush-log-at-trx-commit=2")

            cmd_opts.extend([
                "--big-tables",
                # TODO: warn about hugetlbfs mount and sysctl setup
                #"--large-pages",
                "--innodb-file-per-table",
                "--innodb-flush-method=O_DIRECT",
                "--innodb-file-format=Barracuda",
                "--skip-innodb-doublewrite",

                "--key-buffer-size=%dM" % (self._buffer_size/1024/1024),
                "--innodb-buffer-pool-size=%dM" % (self._buffer_size/1024/1024),
                "--innodb-log-file-size=32M",
                "--innodb-log-buffer-size=1M",
                "--innodb-autoextend-increment=1",
                "--query-cache-min-res-unit=1k",
                "--query-cache-limit=1M",
                "--query-cache-size=64M",
                "--max-allowed-packet=32M",
            ])

            if is_mariadb:
                cmd_opts.extend([
                    # Only MariaDB
                    "--aria-block-size=1k",
                    "--aria-log-dir-path=%s" % self.getBasePath(),
                    "--aria-log-file-size=32M",
                    "--aria-pagecache-buffer-size=%dM" % (self._buffer_size/1024/1024),
                ])

            if is_new:

                print("Setup new MySQL system databases")

                cmd = ["mysql_install_db"]
                cmd.extend(cmd_opts)
                retcode = subprocess.Popen(cmd,
                                 cwd=self.getBasePath(),
                                 stdout=open(os.devnull, 'w'),
                                 stderr=open(os.devnull, 'w')
                ).wait()
                if retcode:
                    print("Something wrong! Return code: %s" % retcode)
                    return False

            cmd = ["mysqld"]
            cmd.extend(cmd_opts)

            print("Starting up MySQLd...")

            self._mysqld_proc = subprocess.Popen(cmd,
                                                 cwd=self.getBasePath(),
                                                 stdout=open(os.devnull, 'w'),
                                                 stderr=open(os.devnull, 'w')
            )

            print("Wait up 10 sec for it to start...")

            t = 10
            while (t>0):
                sleep(0.1)

                if os.path.exists(self.getSocket()):
                    if self.pingServer():
                        break
                if self._mysqld_proc.poll() is not None:
                    break

                t-= 0.1


            if self._mysqld_proc.poll() is not None:
                print("Something wrong? mysqld exited with: %s" % self._mysqld_proc.poll() )
                self._mysqld_proc = None
                return False

            print("Done")

            self.createDb()
            self.create()

        return True


    def stopMysqld(self):
        if self._mysqld_proc is not None:

            if self._notmeStarted:
                self._notmeStarted = False
                return True

            cmd = [
                "mysqladmin",
                "--socket=%s" % self.getSocket(),
                "shutdown"
            ]

            print("Call MySQLd shutdown")
            subprocess.Popen(cmd).wait()

            t = 10
            while (t>0):
                sleep(0.1)
                if self._mysqld_proc.poll() is not None:
                    break
                t -= 0.1

            if self._mysqld_proc.poll() is None:
                print("Terminate MySQLd")
                self._mysqld_proc.terminate()

                t = 5
                while (t>0):
                    sleep(0.1)
                    if self._mysqld_proc.poll() is not None:
                        break
                    t -= 0.1

            if self._mysqld_proc.poll() is None:
                print("Can't :'(")
                return False

            print("Done")

            self._mysqld_proc = None
            self._socket = None

            return True

        return False


    def getConnection(self, nodb=False):
        """
        @rtype L{pymysqlConnection}
        """
        if not self.startMysqld():
            raise RuntimeError("Can't start mysqld server!")

        if nodb:
            conn = pymysql.connect(unix_socket=self.getSocket(), user=self.getUser(), passwd=self.getPassword())
        else:

            if self._conn:
                return self._conn

            conn = self._conn = pymysql.connect(
                unix_socket=self.getSocket(),
                user=self.getUser(),
                passwd=self.getPassword(),
                db=self.getDbName())
            self._conn.autocommit(self.getAutocommit())

        cur = conn.cursor()
        if not self.getAutocommit():
            cur.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
        cur.close()

        return conn

    def getCursor(self, new=False):
        if new:
            cur = self.getConnection().cursor(cursor_type)
        else:
            cur = self.getConnection().cursor(cursor_type)
        cur = self.pingDb(cur)
        return cur

    def pingServer(self):
        result = True
        try:
            conn = self.getConnection(True)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
        except pymysql.err.OperationalError:
            result = False
        return result

    def pingDb(self, cursor):
        try:
            cursor.execute('SELECT 1')
        except BrokenPipeError:
            self.closeConn()
            cursor = self.getConnection().cursor(cursor_type)
            pass
        return cursor

    def createDb(self):

        conn = self.getConnection(True)

        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS `%s` COLLATE utf8_bin;" % self.getDbName())
        cur.close()

        conn.close()
        return True

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

    def closeConn(self):
        if self._conn:
            self._conn.close()
            self._conn = None
        return self

    def close(self):
        self.closeConn()
        if self._mysqld_proc is not None:
            self.stopMysqld()
        return self

    def getSize(self):
        s = 0
        for name, t in self._table.items():
            s += t.getSize()
        return s

    def getFileSize(self):
        s = 0
        for name in self.tables:
            t = self.getTable(name)
            s += t.getFileSize()
        return s

    def getOperationsCount(self):
        s = 0
        for name in self.tables:
            t = self.getTable(name)
            s += t.getAllOperationsCount()
        return s

    def getTimeSpent(self):
        s = 0
        for name in self.tables:
            t = self.getTable(name)
            s += t.getAllTimeSpent()
        return s

    def create(self):
        for t in self.tables:
            self.getTable(t).create()
        return self