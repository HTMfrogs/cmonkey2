"""database.py - mapping cmonkey_run.db files with SQLAlchemy"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship, sessionmaker

# http://docs.sqlalchemy.org/en/latest/core/engines.html#sqlalchemy.create_engine

def make_sqlite_url(path):
    return 'sqlite:///' + path

Base = declarative_base()

class RunInfo(Base):
    __tablename__ = 'run_infos'

    rowid = Column(Integer, primary_key=True)
    start_time = Column(DateTime)
    finish_time = Column(DateTime)
    num_iterations = Column(Integer)
    last_iteration = Column(Integer)
    organism = Column(String)
    species = Column(String)
    ncbi_code = Column(Integer)
    num_rows = Column(Integer)
    num_columns = Column(Integer)
    num_clusters = Column(Integer)
    git_sha = Column(String)

    def __repr__(self):
        return "RunInfo(organism: '%s', # iter= %d, start: %s, finish: %s)" % (self.organism,
                                                                               self.num_iterations,
                                                                               str(self.start_time),
                                                                               str(self.finish_time))

class ClusterStat(Base):
    __tablename__ = 'cluster_stats'

    rowid     = Column(Integer, primary_key=True)
    iteration = Column(Integer, index=True)
    cluster   = Column(Integer)
    num_rows  = Column(Integer)
    num_cols  = Column(Integer)
    residual  = Column(Float)

    def __repr__(self):
        return "ClusterStat(cluster: %d, # rows = %d, # cols = %d resid: %f)" % (self.cluster,
                                                                                  self.num_rows,
                                                                                  self.num_cols,
                                                                                  self.residual)

class StatsType(Base):
    __tablename__ = 'statstypes'

    rowid = Column(Integer, primary_key=True)
    category = Column(String)
    name = Column(String)

    def __repr__(self):
        return "StatsType(category = %s name: %s)" % (self.category, self.name)


class IterationStat(Base):
    __tablename__ = 'iteration_stats'

    rowid = Column(Integer, primary_key=True)
    statstype = Column(Integer, ForeignKey('statstypes.rowid'))
    statstype_obj = relationship('StatsType')
    iteration = Column(Integer)
    score = Column(Float)

    def __repr__(self):
        return "IterationStat(statstype = %s iteration: %d, score: %f)" % (self.statstype_obj.name, self.iteration, self.score)


class RowName(Base):
    __tablename__ = 'row_names'

    rowid = Column(Integer, primary_key=True)
    order_num = Column(Integer)
    name = Column(String, index=True, unique=True)

    def __repr__(self):
        return "RowName(order_num = %d name: %s)" % (self.order_num, self.name)


class ColumnName(Base):
    __tablename__ = 'column_names'

    rowid = Column(Integer, primary_key=True)
    order_num = Column(Integer)
    name = Column(String)

    def __repr__(self):
        return "ColumnName(order_num = %d name: %s)" % (self.order_num, self.name)


class RowMember(Base):
    __tablename__ = 'row_members'

    rowid = Column(Integer, primary_key=True)
    iteration = Column(Integer, index=True)
    cluster = Column(Integer, index=True)
    order_num = Column(Integer, ForeignKey('row_names.order_num'), index=True)
    row_name = relationship('RowName')

    def __repr__(self):
        return "RowMember(iteration = %d cluster: %d row name: %s)" % (self.iteration, self.cluster, self.row_name.name)


class ColumnMember(Base):
    __tablename__ = 'column_members'

    rowid = Column(Integer, primary_key=True)
    iteration = Column(Integer, index=True)
    cluster = Column(Integer)
    order_num = Column(Integer, ForeignKey('column_names.order_num'))
    column_name = relationship('ColumnName')

    def __repr__(self):
        return "ColumnMember(iteration = %d cluster: %d col name: %s)" % (self.iteration, self.cluster, self.column_name.name)


class GlobalBackground(Base):
    __tablename__ = 'global_background'

    rowid = Column(Integer, primary_key=True)
    subsequence = Column(String)
    pvalue = Column(Float)

    def __repr__(self):
        return "GlobalBackground(subsequence: %s, pvalue: %f)" % (self.subsequence, self.pvalue)


class MotifInfo(Base):
    __tablename__ = 'motif_infos'

    rowid = Column(Integer, primary_key=True)
    iteration = Column(Integer)
    cluster = Column(Integer, index=True)
    seqtype = Column(String)
    motif_num = Column(Integer)
    evalue = Column(Float)
    pssm_rows = relationship("MotifPSSMRow")

    def __repr__(self):
        return "MotifInfo(iteration: %d, cluster: %d seqtype: %s motif_num: %d evalue: %f)" % (self.iteration,
                                                                                               self.cluster,
                                                                                               self.seqtype,
                                                                                               self.motif_num,
                                                                                               self.evalue)


class MotifPSSMRow(Base):
    __tablename__ = 'motif_pssm_rows'

    rowid = Column(Integer, primary_key=True)
    motif_info_id = Column(Integer, ForeignKey('motif_infos.rowid'))
    motif_info = relationship('MotifInfo')
    iteration = Column(Integer)
    row = Column(Integer)
    a = Column(Float)
    c = Column(Float)
    g = Column(Float)
    t = Column(Float)

    def __repr__(self):
        return "MotifPSSMRow(iteration: %d, cluster: %d row: %d a: %f c: %f g: %f t: %f)" % (self.iteration,
                                                                                             self.motif_info.cluster,
                                                                                             self.row,
                                                                                             self.a, self.c, self.g, self.t)


class MemeMotifSite(Base):
    __tablename__ = 'meme_motif_sites'

    rowid = Column(Integer, primary_key=True)
    motif_info_id = Column(Integer, ForeignKey('motif_infos.rowid'))
    motif_info = relationship('MotifInfo')
    seq_name = Column(String)
    reverse = Column(Boolean)
    start = Column(Integer)
    pvalue = Column(Float)
    flank_left = Column(String)
    flank_right = Column(String)
    seq = Column(String)

    def __repr__(self):
        return "MemeMotifSite(cluster: %d seqname: %s, reverse: %d, start: %d pvalue: %f flank_left: %s flank_right: %s seq: %s)" % (
            self.motif_info.cluster, self.seq_name, self.reverse, self.start, self.pvalue,
            self.flank_left, self.flank_right, self.seq)


class TomtomResult(Base):
    __tablename__ = 'tomtom_results'

    rowid = Column(Integer, primary_key=True)
    motif_info_id1 = Column(Integer, ForeignKey('motif_infos.rowid'))
    motif_info_id2 = Column(Integer, ForeignKey('motif_infos.rowid'))
    motif_info1 = relationship('MotifInfo', foreign_keys='TomtomResult.motif_info_id1')
    motif_info2 = relationship('MotifInfo', foreign_keys='TomtomResult.motif_info_id2')
    pvalue = Column(Float)

    def __repr__(self):
        return "TomtomResult(motif 1: %d motif 2: %d pvalue: %f)" % (
            self.motif_info1.motif_num, self.motif_info2.motif_num, self.pvalue)


class MotifAnnotation(Base):
    __tablename__ = 'motif_annotations'

    rowid = Column(Integer, primary_key=True)
    motif_info_id = Column(Integer, ForeignKey('motif_infos.rowid'))
    motif_info = relationship('MotifInfo')
    iteration = Column(Integer)
    gene_num = Column(Integer, ForeignKey('row_names.order_num'))
    gene = relationship('RowName')
    position = Column(Integer)
    reverse = Column(Boolean)
    pvalue = Column(Float)

    def __repr__(self):
        return "MotifAnnotation(motif: %d iteration: %d gene: %s position: %d reverse: %d pvalue: %f)" % (
            self.motif_info.motif_num, self.iteration, self.gene.name, self.position, self.reverse,
            self.pvalue)


def make_session(path):
    dburl = make_sqlite_url(path)
    engine = create_engine(dburl)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session