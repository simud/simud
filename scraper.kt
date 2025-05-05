package it.dogior.hadEnough

import com.lagradost.cloudstream3.app
import com.lagradost.cloudstream3.utils.AppUtils.parseJson
import com.lagradost.cloudstream3.utils.ExtractorLink
import com.lagradost.cloudstream3.utils.ExtractorLinkType
import com.lagradost.cloudstream3.utils.Qualities
import kotlinx.coroutines.runBlocking
import okhttp3.HttpUrl.Companion.toHttpUrl
import java.io.File
import android.util.Log

fun main() = runBlocking {
    val extractor = StreamingCommunityExtractor()
    val searcher = StreamingCommunity()

    // Lista dei 10 film Marvel da cercare
    val marvelMovies = listOf(
        "Iron Man",
        "The Avengers",
        "Captain America: The Winter Soldier",
        "Guardians of the Galaxy",
        "Avengers: Age of Ultron",
        "Ant-Man",
        "Captain America: Civil War",
        "Doctor Strange",
        "Spider-Man: Homecoming",
        "Avengers: Infinity War"
    )

    // File M3U8 di output
    val m3u8File = File("streaming.m3u8")
    val m3u8Content = StringBuilder("#EXTM3U\n")

    marvelMovies.forEach { movie ->
        try {
            println("Searching for: $movie")
            Log.d("MarvelExtractor", "Searching for: $movie")

            // Cerca il film
            val searchResults = searcher.search(movie)
            val movieResult = searchResults.find { it.name.contains(movie, ignoreCase = true) }

            if (movieResult != null) {
                println("Found: ${movieResult.name} - ${movieResult.url}")
                Log.d("MarvelExtractor", "Found: ${movieResult.name} - ${movieResult.url}")

                // Carica i dettagli del film
                val loadResponse = searcher.load(movieResult.url)
                val dataUrl = when (loadResponse) {
                    is com.lagradost.cloudstream3.MovieLoadResponse -> loadResponse.dataUrl
                    else -> null
                }

                if (dataUrl != null) {
                    println("Extracting stream for: ${movieResult.name}")
                    Log.d("MarvelExtractor", "Extracting stream for: ${movieResult.name}")

                    // Estrai il link di streaming
                    val links = mutableListOf<ExtractorLink>()
                    extractor.getUrl(
                        url = dataUrl,
                        referer = searcher.mainUrl,
                        subtitleCallback = { /* Ignora i sottotitoli */ },
                        callback = { link -> links.add(link) }
                    )

                    if (links.isNotEmpty()) {
                        val streamUrl = links.first().url
                        m3u8Content.append("#EXTINF:-1,${movieResult.name}\n")
                        m3u8Content.append("$streamUrl\n")
                        println("Stream added for: ${movieResult.name}")
                        Log.d("MarvelExtractor", "Stream added for: ${movieResult.name}")
                    } else {
                        println("No stream found for: ${movieResult.name}")
                        Log.w("MarvelExtractor", "No stream found for: ${movieResult.name}")
                    }
                } else {
                    println("No data URL found for: ${movieResult.name}")
                    Log.w("MarvelExtractor", "No data URL found for: ${movieResult.name}")
                }
            } else {
                println("Movie not found: $movie")
                Log.w("MarvelExtractor", "Movie not found: $movie")
            }
        } catch (e: Exception) {
            println("Error processing $movie: ${e.message}")
            Log.e("MarvelExtractor", "Error processing $movie", e)
        }
    }

    // Scrivi il file M3U8
    m3u8File.writeText(m3u8Content.toString())
    println("M3U8 file generated: streaming.m3u8")
    Log.d("MarvelExtractor", "M3U8 file generated: streaming.m3u8")
}
