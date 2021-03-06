# -*- coding: utf8 -*-

__author__ = 'sergey'

from dedupsqlfs.db.sqlite.table import Table

class TableOption( Table ):

    _table_name = "option"

    def create( self ):
        c = self.getCursor()

        # Create table
        c.execute(
            "CREATE TABLE IF NOT EXISTS `%s` (" % self._table_name+
                "name TEXT NOT NULL PRIMARY KEY, "+
                "value TEXT NULL"+
            ")"
        )
        return

    def insert( self, name, value ):
        self.startTimer()
        cur = self.getCursor()
        cur.execute("INSERT INTO `%s`(name, value) VALUES (?, ?)" % self._table_name, (name, value))
        item = cur.lastrowid
        self.stopTimer('insert')
        return item

    def update( self, name, value ):
        """
        @return: count updated rows
        @rtype: int
        """
        self.startTimer()
        cur = self.getCursor()
        cur.execute("UPDATE `%s` SET value=? WHERE name=?" % self._table_name, (value, name))
        count = cur.rowcount
        self.stopTimer('update')
        return count

    def get( self, name, raw=False ):
        self.startTimer()
        cur = self.getCursor()
        cur.execute("SELECT value FROM `%s` WHERE name=:name" % self._table_name,
                {"name": name}
        )
        item = cur.fetchone()
        if item:
            if raw:
                item = item["value"]
            else:
                item = item["value"].decode()
        self.stopTimer('get')
        return item

    def getAll( self ):
        self.startTimer()
        cur = self.getCursor()
        cur.execute("SELECT * FROM `%s`" % self._table_name)
        items = cur.fetchall()
        opts = {}
        for item in items:
            opts[ item["name"].decode() ] = item["value"].decode()
        self.stopTimer('getAll')
        return opts

    pass
