const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const { spawn } = require('child_process');

(async () => {
    // Configurazione
    const url = process.env.TARGET_URL || 'https://streamingcommunity.spa/watch/314';
    const outputFile = 'streaming.m3u8';
    const playButtonSelector = process.env.PLAY_BUTTON_SELECTOR || '#play-button';

    // Avvia il browser
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium'
    });
    const page = await browser.newPage();

    // Imposta User-Agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

    // Intercetta le richieste di rete
    await page.setRequestInterception(true);
    const m3u8Links = new Set();

    page.on('request', request => {
        const requestUrl = request.url();
        if (requestUrl.includes('.m3u8')) {
            console.log(`Flusso M3U8 trovato: ${requestUrl}`);
            m3u8Links.add(requestUrl);
        }
        request.continue();
    });

    try {
        // Naviga al sito
        console.log(`Navigazione verso ${url}`);
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

        // Salva uno screenshot per il debug
        await page.screenshot({ path: 'debug_screenshot.png', fullPage: true });
        console.log('Screenshot salvato come debug_screenshot.png');

        // Verifica se il pulsante play esiste
        console.log(`Attendo il selettore: ${playButtonSelector}`);
        const playButton = await page.$(playButtonSelector);
        if (playButton) {
            console.log('Pulsante play trovato, clicco...');
            await page.click(playButtonSelector);
        } else {
            console.log('Pulsante play non trovato, il video potrebbe avviarsi automaticamente.');
        }

        // Aspetta 10 secondi per il caricamento del video
        await new Promise(resolve => setTimeout(resolve, 10000));

        // Salva i link trovati
        if (m3u8Links.size === 0) {
            console.log('Nessun flusso M3U8 trovato.');
        } else {
            const links = Array.from(m3u8Links).join('\n');
            await fs.writeFile(outputFile, links);
            console.log(`Trovati ${m3u8Links.size} flussi M3U8. Salvati in ${outputFile}`);
        }

        // Opzionale: scarica il primo flusso con FFmpeg
        if (m3u8Links.size > 0) {
            const firstLink = Array.from(m3u8Links)[0];
            console.log(`Tentativo di scaricare il flusso: ${firstLink}`);
            const ffmpeg = spawn('ffmpeg', [
                '-headers', 'Referer: https://streamingcommunity.spa',
                '-i', firstLink,
                '-c', 'copy',
                'output.mp4'
            ]);

            ffmpeg.stderr.on('data', (data) => {
                console.error(`FFmpeg errore: ${data}`);
            });

            ffmpeg.on('close', (code) => {
                console.log(`FFmpeg terminato con codice ${code}`);
            });

            // Aspetta che FFmpeg finisca (semplificazione)
            await new Promise(resolve => setTimeout(resolve, 30000));
        }

    } catch (error) {
        console.error(`Errore durante l'esecuzione: ${error.message}`);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();