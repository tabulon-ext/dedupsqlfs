# -*- coding: utf8 -*-
#
# DB migration 001 by 2016-01-22
#
# - Rename current ZSTD compression into 'zstd036'
# - Add new 'zstd' compression for 0.4+
#
__author__ = 'sergey'

__NUMBER__ = 20160122001


def run(manager):
    """
    :param manager: Database manager
    :type  manager: dedupsqlfs.db.sqlite.manager.DbManager|dedupsqlfs.db.mysql.manager.DbManager
    :return: bool
    """

    try:
        table_ct = manager.getTable("compression_type")
        """
        :type table_ct: dedupsqlfs.db.sqlite.table.compression_type.TableCompressionType |
                        dedupsqlfs.db.mysql.table.compression_type.TableCompressionType
        """

        if not table_ct.find('zstd036'):
            cur = table_ct.getCursor()

            cur.execute("UPDATE compression_type SET value='zstd036' WHERE value='zstd';")
            cur.execute("INSERT INTO compression_type (value) VALUES ('zstd');")

            table_ct.commit()
    except Exception as e:
        manager.getLogger().error("Migration #%s error: %s" % (__NUMBER__, e,))
        return False

    table_opts = manager.getTable("option")

    table_opts.getCursor()
    mignumber = table_opts.get("migration")
    if not mignumber:
        table_opts.insert("migration", __NUMBER__)
    else:
        table_opts.update("migration", __NUMBER__)

    table_opts.commit()

    return True
