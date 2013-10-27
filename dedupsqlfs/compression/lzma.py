# -*- coding: utf8 -*-

__author__ = 'sergey'

"""
Class for LZMA compression helper
"""

from dedupsqlfs.compression import BaseCompression

class LzmaCompression(BaseCompression):

    _method_name = "lzma"

    _minimal_size = 69

    _has_comp_level_options = True

    def getFastCompressionOptions(self):
        return {
            "preset": 1,
        }

    def getNormCompressionOptions(self):
        return {
            "preset": 4,
        }

    def getBestCompressionOptions(self):
        return {
            "preset": 7,
        }

    pass
