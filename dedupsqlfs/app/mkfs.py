# -*- coding: utf8 -*-

# Imports. {{{1

import sys

# Try to load the required modules from Python's standard library.
try:
    import os
    import argparse
    import time
    import hashlib
    import logging
    from dedupsqlfs.lib import constants
except ImportError as e:
    msg = "Error: Failed to load one of the required Python modules! (%s)\n"
    sys.stderr.write(msg % str(e))
    sys.exit(1)


def mkfs(options, compression_methods=None, hash_functions=None):
    from dedupsqlfs.fuse.dedupfs import DedupFS
    from dedupsqlfs.fuse.operations import DedupOperations

    ops = DedupOperations()
    _fuse = DedupFS(
        ops, None,
        options,
        use_ino=True, default_permissions=True, fsname="dedupsqlfs")

    _fuse.saveCompressionMethods(compression_methods)

    for modname in compression_methods:
        if modname == constants.COMPRESSION_TYPE_NONE:
            continue
        module = __import__(modname)
        _fuse.appendCompression(modname, getattr(module, "compress"), getattr(module, "decompress"))

    _fuse.setOption("gc_umount_enabled", False)
    _fuse.setOption("gc_vacuum_enabled", False)
    _fuse.setOption("gc_enabled", False)

    _fuse.operations.init()
    _fuse.operations.destroy()
    return 0

def main(): # {{{1
    """
    This function enables using dedupsqlfs.py as a shell script that creates FUSE
    mount points. Execute "dedupsqlfs -h" for a list of valid command line options.
    """

    logger = logging.getLogger("mkfs.dedupsqlfs[main]")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stderr))

    parser = argparse.ArgumentParser(conflict_handler="resolve")

    # Register some custom command line options with the option parser.
    option_stored_in_db = " (this option is only useful when creating a new database, because your choice is stored in the database and can't be changed after that)"

    parser.add_argument('-h', '--help', action='help', help="show this help message followed by the command line options defined by the Python FUSE binding and exit")
    parser.add_argument('-v', '--verbose', action='count', dest='verbosity', default=0, help="increase verbosity")
    parser.add_argument('--log-file', dest='log_file', help="specify log file location")
    parser.add_argument('--data', dest='data', metavar='DIRECTORY', default="~/data", help="Specify the base location for the files in which metadata and blocks data is stored. Defaults to ~/data")
    parser.add_argument('--name', dest='name', metavar='DATABASE', default="dedupsqlfs", help="Specify the name for the database directory in which metadata and blocks data is stored. Defaults to dedupsqlfs")
    parser.add_argument('--temp', dest='temp', metavar='DIRECTORY', help="Specify the location for the files in which temporary data is stored. By default honour TMPDIR environment variable value.")
    parser.add_argument('--block-size', dest='block_size', metavar='BYTES', default=1024*128, type=int, help="Specify the maximum block size in bytes" + option_stored_in_db + ". Defaults to 128kB.")
    parser.add_argument('--nosync', dest='synchronous', action='store_false', help="Disable SQLite's normal synchronous behavior which guarantees that data is written to disk immediately, because it slows down the file system too much (this means you might lose data when the mount point isn't cleanly unmounted).")

    # Dynamically check for supported hashing algorithms.
    msg = "Specify the hashing algorithm that will be used to recognize duplicate data blocks: one of %s"
    hash_functions = list({}.fromkeys([h.lower() for h in hashlib.algorithms_available]).keys())
    hash_functions.sort()
    msg %= ', '.join('%r' % fun for fun in hash_functions)
    msg += option_stored_in_db + ". Defaults to 'sha1'. Data can be rehashed by do.dedupsqlfs @todo."
    parser.add_argument('--hash', dest='hash_function', metavar='FUNCTION', choices=hash_functions, default='md5', help=msg)

    # Dynamically check for supported compression methods.
    compression_methods = [constants.COMPRESSION_TYPE_NONE]
    for modname in constants.COMPRESSION_SUPPORTED:
        try:
            module = __import__(modname)
            if hasattr(module, 'compress') and hasattr(module, 'decompress'):
                compression_methods.append(modname)
        except ImportError:
            pass
    if len(compression_methods) > 1:
        compression_methods.append(constants.COMPRESSION_TYPE_BEST)
        compression_methods.append(constants.COMPRESSION_TYPE_CUSTOM)

    msg = "enable compression of data blocks using one of the supported compression methods: one of %s"
    msg %= ', '.join('%r' % mth for mth in compression_methods)
    msg += ". Defaults to %r." % constants.COMPRESSION_TYPE_NONE
    parser.add_argument('--compress', dest='compression_method', metavar='METHOD', choices=compression_methods, default=constants.COMPRESSION_TYPE_NONE, help=msg)
    parser.add_argument('--force-compress', dest='compression_forced', action="store_true", help="Force compression event if resulting data is bigger than original.")
    parser.add_argument('--custom-compress', dest='compression_custom', metavar='METHOD', choices=compression_methods, action="append", help=msg)
    parser.add_argument('--minimal-compress-size', dest='compression_minimal_size', metavar='BYTES', type=int, default=64, help="Minimal block data size for compression. Defaults to 64 bytes. Do not do compression if not forced to.")

    # Dynamically check for profiling support.
    try:
        # Using __import__() here because of pyflakes.
        for p in 'cProfile', 'pstats': __import__(p)
        parser.add_argument('--profile', action='store_true', default=False, help="Use the Python modules cProfile and pstats to create a profile of time spent in various function calls and print out a table of the slowest functions at exit (of course this slows everything down but it can nevertheless give a good indication of the hot spots).")
    except ImportError:
        logger.warning("No profiling support available, --profile option disabled.")
        logger.warning("If you're on Ubuntu try 'sudo apt-get install python-profiler'.")

    args = parser.parse_args()

    # Do not want 'best' after help setup
    compression_methods.pop()
    compression_methods.pop()

    if args.profile:
        sys.stderr.write("Enabling profiling..\n")
        import cProfile, pstats
        profile = '.dedupsqlfs.cprofile-%i' % time.time()
        cProfile.run('mkfs(args, compression_methods, hash_functions)', profile)
        sys.stderr.write("\n Profiling statistics:\n\n")
        s = pstats.Stats(profile)
        s.sort_stats('time')
        s.print_stats(0.1)
        os.unlink(profile)
    else:
        return mkfs(args, compression_methods, hash_functions)

    return 0

# vim: ts=4 sw=4 et
