# vi: sw=4 ts=4 et:
"""organism.py - organism-specific functionality in cMonkey

This file is part of cMonkey Python. Please see README and LICENSE for
more information and licensing details.
"""
import logging
import util
import StringIO
import re
import patches
import os

#RSAT_BASE_URL = 'http://embnet.ccg.unam.mx/rsa-tools'
#RSAT_BASE_URL = 'http://rsat.bigre.ulb.ac.be/rsat/'

class RsatFiles:
    """This class implements the same service functions as RsatDatabase, but
    takes the data from files"""
    def __init__(self, dirname, basename, taxonomy_id, feature_name, url):
        self.dirname = dirname
        self.taxonomy_id = taxonomy_id
        self.basename = basename
        self.feature_name = feature_name
        self.url = url

    def get_taxonomy_id(self, organism):
        return self.taxonomy_id

    def get_rsat_organism(self, kegg_organism):
        return self.basename

    def get_rsat_getURL(self):
        return self.url

    def get_rsat_featureName(self):
        return self.featureName

    def get_features(self, organism, original=True):
        if original:
            #path = os.path.join(self.dirname, 'features.tab')
            path = os.path.join(self.dirname, self.feature_name + '.tab')
        else:
            path = os.path.join(self.dirname, organism + '_' + self.feature_name)
        with open(path) as infile:
            return infile.read()

    def get_feature_names(self, organism, original=True):
        if original:
            path = os.path.join(self.dirname, self.feature_name + '_names.tab')
        else:
            path = os.path.join(self.dirname, organism + '_' + self.feature_name + '_names')
        with open(path) as infile:
            return infile.read()

    def get_contig_sequence(self, organism, contig, original=True):
        if original:
            path = os.path.join(self.dirname, contig + '.tab')
        else:
            path = os.path.join(self.dirname, organism + '_' + contig)
        with open(path) as infile:
            seqstr = infile.read().upper()
            return join_contig_sequence(seqstr)


class RsatDatabase:
    """abstract interface to access an RSAT mirror"""
    DIR_PATH = 'data/genomes'
    ORGANISM_PATH = 'genome/organism.tab'
    ORGANISM_NAMES_PATH = 'genome/organism_names.tab'
    #FEATURE_PATH = 'genome/feature.tab'
    #FEATURE_NAMES_PATH = 'genome/feature_names.tab'

    def __init__(self, base_url, cache_dir, feature_name):
        """create an RsatDatabase instance based on a mirror URL"""
        self.base_url = base_url
        self.cache_dir = cache_dir.rstrip('/')
	self.feature_name = feature_name
	self.feature_path = 'genome/' + feature_name + '.tab'
	self.feature_names_path = 'genome/' + feature_name + '_names.tab'

    def get_rsat_organism(self, kegg_organism):
        """returns the HTML page for the directory listing"""
        logging.info('RSAT - get_directory()')
        cache_file = "/".join([self.cache_dir, 'rsat_dir.html'])
        text = util.read_url_cached("/".join([self.base_url,
                                              RsatDatabase.DIR_PATH]),
                                    cache_file)
        return util.best_matching_links(kegg_organism, text)[0].rstrip('/')

    def get_taxonomy_id(self, organism):
        """returns the specified organism name file contents"""
        logging.info('RSAT - get_organism_names(%s)', organism)
        cache_file = "/".join([self.cache_dir, 'rsatnames_' + organism])
        text = util.read_url_cached(
            "/".join([self.base_url, RsatDatabase.DIR_PATH, organism,
                      RsatDatabase.ORGANISM_NAMES_PATH]), cache_file)
        organism_names_dfile = util.dfile_from_text(text, comment='--')
        return patches.patch_ncbi_taxonomy(organism_names_dfile.lines[0][0])

    def get_features(self, organism):
        """returns the specified organism's feature file contents
        Note: the current version only tries to read from feature.tab
        while the original cMonkey will fall back to cds.tab
        if that fails
        """
        #logging.info('RSAT - get_features(%s)', organism)
        cache_file = "/".join([self.cache_dir, organism + '_' + self.feature_name])
        return util.read_url_cached("/".join([self.base_url,
                                              RsatDatabase.DIR_PATH,
                                              organism,
                                              self.feature_path]),
                                    cache_file)

    def get_feature_names(self, organism):
        """returns the specified organism's feature name file contents"""
        #logging.info('RSAT - get_feature_names(%s)', organism)
        cache_file = "/".join([self.cache_dir, organism + '_' + self.feature_name + '_names'])
        return util.read_url_cached(
            "/".join([self.base_url,
                      RsatDatabase.DIR_PATH,
                      organism,
                      self.feature_names_path]),
            cache_file)

    def get_contig_sequence(self, organism, contig):
        """returns the specified contig sequence"""
        #logging.info('RSAT - get_contig_sequence(%s, %s)',
        #             organism, contig)
        cache_file = "/".join([self.cache_dir, organism + '_' + contig])
        url = "/".join([self.base_url, RsatDatabase.DIR_PATH, organism,
                        'genome', contig + '.raw'])
        seqstr = util.read_url_cached(url, cache_file).upper()
        return join_contig_sequence(seqstr)


def join_contig_sequence(seqstr):
    """we take the safer route and assume that the input could
    be separated out into lines"""
    buf = StringIO.StringIO(seqstr)
    result = ''
    for line in buf:
        result += line.strip()
    return result

__all__ = ['RsatDatabase']
