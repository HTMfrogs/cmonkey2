package controllers

import play.api._
import play.api.mvc._
import play.api.libs.json._
import java.io._
import java.util.regex._
import scala.collection.mutable.HashMap
import scala.collection.mutable.ArrayBuffer
import scala.collection.JavaConversions._

// Formatter object for creating common Javascript constructs
object Formatter {
  def formatStrings(strs: Seq[String]) = {
    "[%s]".format(strs.map(squote).mkString(", "))
  }
  def formatFloats(vals: Seq[Float]) = {
    "[%s]".format(vals.mkString(", "))
  }
  def formatInts(vals: Seq[Int]) = {
    "[%s]".format(vals.mkString(", "))
  }

  private def squote(value: Any): String = "'%s'".format(value.toString)

  def toHSSeries(ratios: RatioMatrix) = {
    val builder = new StringBuilder
    builder.append("[")
    println("# rows: " + ratios.rows.length)
    for (row <- 0 until ratios.rows.length) {
      if (row > 0) builder.append(", ")
      builder.append(toHSSeriesEntry(ratios.rows(row), ratios.values(row)))
    }
    builder.append("]")
    builder.toString
  }

  private def toHSSeriesEntry(name: String, values: Array[Float]) = {
    "{ name: '%s', data: %s }".format(name, formatFloats(values))
  }

  def toHSSeries(values: Array[Double]) = {
    val builder = new StringBuilder
    builder.append("[ { name: 'mean resid', data: [")
    for (i <- 0 until values.length) {
      if (i > 0) builder.append(", ")
      builder.append("%f".format(values(i)))
    }
    builder.append("] }]")
    builder.toString
  }

  def toNRowNColHSSeries(stats: Map[Int, IterationStats]) = {
    val iterations = stats.keySet.toArray
    java.util.Arrays.sort(iterations)

    val meanRows = new Array[Double](iterations.length)
    val meanColumns = new Array[Double](iterations.length)

    for (i <- 0 until iterations.length) {
      var totalRows = 0.0
      var totalColumns = 0.0
      for (cluster <- stats(iterations(i)).clusters.keys) {
        totalRows += stats(iterations(i)).clusters(cluster).numRows
        totalColumns += stats(iterations(i)).clusters(cluster).numColumns
      }
      val numClusters = stats(iterations(i)).clusters.size
      meanRows(i) = totalRows / numClusters
      meanColumns(i) = totalColumns / numClusters
    }

    // columns
    val builder = new StringBuilder
    builder.append("[ { name: 'columns', data: [")
    for (i <- 0 until iterations.length) {
      if (i > 0) builder.append(", ")
      builder.append("%f".format(meanColumns(i)))
    }
    builder.append("] }, ")

    // rows
    builder.append("{ name: 'rows', data: [")
    for (i <- 0 until iterations.length) {
      if (i > 0) builder.append(", ")
      builder.append("%f".format(meanRows(i)))
    }
    builder.append("] }]")

    builder.toString
  }
}

case class Snapshot(rows: Map[Int, List[String]], columns: Map[Int, List[String]],
                    motifs: Map[Int, Map[String, Array[Array[Array[Float]]]]]) {
  def clusters: Seq[Int] = {
    rows.keys.toSeq.sorted
  }
}

case class ClusterStats(numRows: Int, numColumns: Int, residual: Double)
case class IterationStats(clusters: Map[Int, ClusterStats], medianResidual: Double)

object Application extends Controller {

  val JsonFilePattern = Pattern.compile("(\\d+)-results.json")
  val StatsFilePattern = Pattern.compile("(\\d+)-stats.json")
  val AppConfig = Play.current.configuration
  val ProjectConfigFile = new File("project.conf")
  val ProjectConfig = new java.util.Properties
  ProjectConfig.load(new FileReader(ProjectConfigFile))

  val OutDirectory = new File(ProjectConfig.getProperty("cmonkey.out.directory"))
  val BaseResultsFileName = "%d-results.json"
  val Synonyms = SynonymsFactory.getSynonyms(
    ProjectConfig.getProperty("cmonkey.synonyms.format"),
    ProjectConfig.getProperty("cmonkey.synonyms.file"))
  val RatiosFactory = new RatioMatrixFactory(
    new File(ProjectConfig.getProperty("cmonkey.ratios.file")),
    Synonyms)

  implicit object StatsFormat extends Format[IterationStats] {
    def reads(json: JsValue): IterationStats = {
      val residual = (json \ "median_residual").asInstanceOf[JsNumber].value.doubleValue
      val clusters = (json \ "cluster").as[JsObject]
      val clusterStats = new HashMap[Int, ClusterStats]
      for (field <- clusters.fields) {
        val cstats = field._2.as[JsObject]
        clusterStats(field._1.toInt) = ClusterStats(cstats.value("num_rows").asInstanceOf[JsNumber].value.intValue,
                                                    cstats.value("num_columns").asInstanceOf[JsNumber].value.intValue,
                                                    cstats.value("residual").asInstanceOf[JsNumber].value.doubleValue)
      }
      IterationStats(clusterStats.toMap, residual)
    }
    def writes(snapshot: IterationStats): JsValue = JsUndefined("TODO")
  }

  implicit object SnapshotFormat extends Format[Snapshot] {
    def reads(json: JsValue): Snapshot = {
      val rows = (json \ "rows").as[JsObject]
      val cols = (json \ "columns").as[JsObject]
      val motifsVal = (json \ "motifs")
      val clusterRows = new HashMap[Int, List[String]]
      for (field <- rows.fields) {
        clusterRows(field._1.toInt) = field._2.as[List[String]].map(str => Synonyms(str))
        //println(clusterRows(field._1.toInt))
      }

      val clusterCols = new HashMap[Int, List[String]]
      for (field <- cols.fields) {
        clusterCols(field._1.toInt) = field._2.as[List[String]]
      }

      val clusterMotifs = new HashMap[Int, Map[String, Array[Array[Array[Float]]]]]
      try {
        val motifs = motifsVal.as[JsObject]        
        for (field <- motifs.fields) {
          val cluster = field._1
          val seqTypeObj = field._2.as[JsObject]

          val seqTypeMotifs = new HashMap[String, Array[Array[Array[Float]]]]

          for (stfield <- seqTypeObj.fields) {
            val seqType = stfield._1
            val stMotifs = stfield._2.asInstanceOf[JsArray].value          
            val pssms = stMotifs.map(m => m.asInstanceOf[JsObject].value("pssm").as[Array[Array[Float]]])
            seqTypeMotifs(seqType) = pssms.toArray
          }
          clusterMotifs(field._1.toInt) = seqTypeMotifs.toMap
        }
      } catch {
        case _ => println("\nNo motifs found !!!")
      }
      Snapshot(clusterRows.toMap, clusterCols.toMap, clusterMotifs.toMap)
    }

    def writes(snapshot: Snapshot): JsValue = JsUndefined("TODO")
  }

  private def readSnapshot(iteration: Int): Option[Snapshot] = {
    val pathname = (OutDirectory + "/" + BaseResultsFileName).format(iteration)
    printf("Reading snapshot: %s\n", pathname)
    val infile = new File(pathname)
    if (infile.exists) {
      val in = new BufferedReader(new FileReader(infile))
      val buffer = new StringBuilder
      var line = in.readLine
      while (line != null) {
        buffer.append(line)
        line = in.readLine
      }
      in.close
      Some(play.api.libs.json.Json.parse(buffer.toString).as[Snapshot])
    } else {
      printf("File '%s' does not exist !\n", infile.getName)
      None
    }
  }

  private def availableIterations = {
    val fileNames = OutDirectory.list(new FilenameFilter {
      def accept(dir: File, name: String) = JsonFilePattern.matcher(name).matches
    })
    val result = new ArrayBuffer[Int]
    for (name <- fileNames) {
      val matcher = JsonFilePattern.matcher(name)
      matcher.matches
      result += matcher.group(1).toInt
    }
    result.sortWith((v1: Int, v2: Int) => v1 < v2)
  }

  private def readStats = {
    val files = OutDirectory.listFiles(new FilenameFilter {
      def accept(dir: File, name: String) = StatsFilePattern.matcher(name).matches
    })
    val stats = new HashMap[Int, IterationStats]

    for (i <- 0 until files.length) {
      val file = files(i)
      val in = new BufferedReader(new FileReader(file))
      val buffer = new StringBuilder
      var line = in.readLine
      while (line != null) {
        buffer.append(line)
        line = in.readLine
      }
      in.close

      val statsOption = Some(play.api.libs.json.Json.parse(buffer.toString).as[IterationStats])      
      if (statsOption != None) {
        val matcher = StatsFilePattern.matcher(file.getName)
        matcher.matches
        val iteration = matcher.group(1).toInt
        //result(iteration - 1) = statsOption.get.medianResidual
        stats(iteration) = statsOption.get
      }
    }
    stats
  }

  // **********************************************************************
  // ****** VIEWS
  // **********************************************************************

  def index = index2(1)

  def index2(iteration: Int) = Action {
    val iterations = availableIterations
    println("# Iterations found: " + iterations.length)

    // create sorted results
    val stats = readStats
    val statsIterations = stats.keySet.toArray
    java.util.Arrays.sort(statsIterations)
    val meanResiduals = new Array[Double](stats.size)
    var i = 0
    for (key <- statsIterations) {
      meanResiduals(i) = stats(key).medianResidual
      i += 1
    }

    Ok(views.html.index(readSnapshot(iteration), iterations, iteration,
                        statsIterations, meanResiduals, stats.toMap))
  }

  def cluster(iteration: Int, cluster: Int) = Action {
    val snapshot = readSnapshot(iteration)
    val ratios = RatiosFactory.readRatios(snapshot.get.rows(cluster).toArray)
    val rows    = snapshot.get.rows(cluster)
    val columns = snapshot.get.columns(cluster)
    val pssm = if (snapshot.get.motifs.size > 0) {
      toJsonPssm(snapshot.get.motifs(cluster))
    } else {
      new Array[String](0)
    }
    Ok(views.html.cluster(iteration, cluster, rows, columns, ratios, pssm))
  }

  private def toJsonPssm(stPssms: Map[String, Array[Array[Array[Float]]]]): Array[String] = {
    val result = new java.util.ArrayList[String]
    for (seqType <- stPssms.keys) {
      val pssms = stPssms(seqType)
      printf("SEQ TYPE: %s, # PSSMs: %d\n", seqType, pssms.length)
      for (i <- 0 until pssms.length) {
        result.add(Json.stringify(JsObject(List("alphabet" -> Json.toJson(Array("A", "C", "G", "T")),
                                                "values" -> Json.toJson(pssms(i))))))
      }
    }
    println("# PSSMS: " + result.length)
    result.toArray(new Array[String](0))
  }
}
