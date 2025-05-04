import okhttp3.OkHttpClient
import okhttp3.Request
import org.jsoup.Jsoup
import java.io.File
import java.util.regex.Pattern

object StreamingCommunityScraper {
    private const val BASE_URL = "https://streamingcommunity.spa"
    private const val SEARCH_URL = "$BASE_URL/search"
    private const val OUTPUT_FILE = "streaming.m3u8"
    private const val DEBUG_DIR = "debug"
    private const val NETWORK_LOG = "network_requests.log"

    // Lista dei 10 film Marvel
    private val MARVEL_MOVIES = listOf(
        mapOf("title" to "Iron Man", "year" to 2008),
        mapOf("title" to "The Avengers", "year" to 2012),
        mapOf("title" to "Captain America: The Winter Soldier", "year" to 2014),
        mapOf("title" to "Guardians of the Galaxy", "year" to 2014),
        mapOf("title" to "Avengers: Age of Ultron", "year" to 2015),
        mapOf("title" to "Captain America: Civil War", "year" to 2016),
        mapOf("title" to "Doctor Strange", "year" to 2016),
        mapOf("title" to "Spider-Man: Homecoming", "year" to 2017),
        mapOf("title" to "Black Panther", "year" to 2018),
        mapOf("title" to "Avengers: Endgame", "year" to 2019)
    )

    private val client = OkHttpClient()
    private val m3u8Pattern = Pattern.compile("\"(https?://[^\"]+\\.m3u8)\"")

    fun sanitizeFilename(filename: String): String {
        val invalidChars = "<>:\"/\\|?*\r\n".toSet() + (0..31).map { it.toChar() }
        return filename.map { if (it in invalidChars) '_' else it }.joinToString("")
    }

    fun setupDebugDir() {
        File(DEBUG_DIR).mkdirs()
    }

    fun logNetworkRequest(url: String, status: Int, contentLength: Int) {
        File(NETWORK_LOG).appendText("URL: $url, Status: $status, Content-Length: $contentLength\n")
    }

    fun fetchTitleUrl(title: String, year: Int): String? {
        val query = "$title $year"
        try {
            val request = Request.Builder()
                .url("$SEARCH_URL?q=$query")
                .addHeader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                .addHeader("Referer", BASE_URL)
                .addHeader("Accept", "text/html,application/xhtml+xml")
                .build()
            client.newCall(request).execute().use { response ->
                val body = response.body?.string() ?: return null
                logNetworkRequest(request.url.toString(), response.code, body.length)

                // Salva la pagina di ricerca per debug
                val debugFile = "$DEBUG_DIR/search_${sanitizeFilename(title)}_$year.html"
                File(debugFile).writeText(body)

                val doc = Jsoup.parse(body)
                val selectors = listOf(
                    ".card a[href*='/titles/']",
                    ".media a[href*='/titles/']",
                    ".search-result a[href*='/titles/']",
                    ".film-card a[href*='/titles/']",
                    "a[href*='/titles/']"
                )
                for (selector in selectors) {
                    val result = doc.selectFirst(selector)
                    if (result != null) {
                        val titleUrl = result.attr("href").let {
                            if (it.startsWith("http")) it else "$BASE_URL$it"
                        }
                        // Estrai l'ID da /titles/<id>-<slug>
                        val idMatch = Regex("""/titles/(\d+)-""").find(titleUrl)
                        if (idMatch != null) {
                            val movieId = idMatch.groupValues[1]
                            val watchUrl = "$BASE_URL/watch/$movieId"
                            println("Trovato URL per '$title': $watchUrl")
                            return watchUrl
                        }
                    }
                }
                println("Nessun risultato trovato per '$title' con i selettori: $selectors")
                return null
            }
        } catch (e: Exception) {
            println("Errore nella ricerca di '$title ($year)': ${e.message}")
            return null
        }
    }

    fun extractStreamUrl(pageUrl: String): String? {
        try {
            val request = Request.Builder()
                .url(pageUrl)
                .addHeader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                .addHeader("Referer", BASE_URL)
                .addHeader("Accept", "text/html,application/xhtml+xml")
                .build()
            client.newCall(request).execute().use { response ->
                val body = response.body?.string() ?: return null
                logNetworkRequest(pageUrl, response.code, body.length)

                // Salva la pagina del contenuto per debug
                val pageId = pageUrl.split("/").last()
                val debugFile = "$DEBUG_DIR/content_$pageId.html"
                File(debugFile).writeText(body)

                val doc = Jsoup.parse(body)

                // Cerca negli script
                doc.select("script").forEach { script ->
                    script.data().takeIf { it.contains("m3u8") }?.let { data ->
                        m3u8Pattern.matcher(data).takeIf { it.find() }?.let { matcher ->
                            val m3u8Url = matcher.group(1)
                            println("Trovato M3U8 in script: $m3u8Url")
                            return m3u8Url
                        }
                    }
                }

                // Cerca un iframe del player
                doc.selectFirst("iframe[src*='player']")?.let { iframe ->
                    val iframeUrl = iframe.attr("src").let {
                        if (it.startsWith("http")) it else "$BASE_URL$it"
                    }
                    client.newCall(Request.Builder().url(iframeUrl).build()).execute().use { iframeResponse ->
                        val iframeBody = iframeResponse.body?.string() ?: return@let
                        logNetworkRequest(iframeUrl, iframeResponse.code, iframeBody.length)

                        // Salva l'iframe per debug
                        val iframeDebugFile = "$DEBUG_DIR/iframe_$pageId.html"
                        File(iframeDebugFile).writeText(iframeBody)

                        m3u8Pattern.matcher(iframeBody).takeIf { it.find() }?.let { matcher ->
                            val m3u8Url = matcher.group(1)
                            println("Trovato M3U8 in iframe: $m3u8Url")
                            return m3u8Url
                        }
                    }
                }

                // Cerca un'API del player
                val apiMatch = Regex(""""playerApi":"(https?://[^"]+)"""").find(body)
                if (apiMatch != null) {
                    val apiUrl = apiMatch.groupValues[1]
                    client.newCall(Request.Builder().url(apiUrl).build()).execute().use { apiResponse ->
                        val apiBody = apiResponse.body?.string() ?: return@let
                        logNetworkRequest(apiUrl, apiResponse.code, apiBody.length)
                        try {
                            val json = org.json.JSONObject(apiBody)
                            val m3u8Url = json.optString("m3u8_url") ?: json.optString("url") ?: json.optString("hls")
                            if (m3u8Url.endsWith(".m3u8")) {
                                println("Trovato M3U8 in API: $m3u8Url")
                                return m3u8Url
                            }
                        } catch (e: Exception) {
                            println("Risposta API non valida per $apiUrl: ${e.message}")
                        }
                    }
                }

                println("Nessun M3U8 trovato per $pageUrl")
                return null
            }
        } catch (e: Exception) {
            println("Errore nell'estrazione del flusso per $pageUrl: ${e.message}")
            return null
        }
    }

    fun generateM3u8() {
        setupDebugDir()
        File(NETWORK_LOG).delete()
        val streams = mutableListOf<Pair<String, String>>()
        MARVEL_MOVIES.forEach { movie ->
            val title = movie["title"] as String
            val year = movie["year"] as Int
            println("Cercando '$title ($year)'...")
            val pageUrl = fetchTitleUrl(title, year)
            if (pageUrl != null) {
                val streamUrl = extractStreamUrl(pageUrl)
                if (streamUrl != null) {
                    streams.add(title to streamUrl)
                    println("Flusso trovato per '$title'")
                } else {
                    println("Nessun flusso trovato per '$title'")
                }
            } else {
                println("Film '$title' non trovato")
            }
        }

        File(OUTPUT_FILE).writeText("#EXTM3U\n" + streams.joinToString("") { (title, url) ->
            "#EXTINF:-1,$title\n$url\n"
        })
        println("File $OUTPUT_FILE generato con ${streams.size} flussi.")
    }
}

fun main() {
    StreamingCommunityScraper.generateM3u8()
}