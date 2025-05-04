const puppeteer = require('puppeteer');
const fs = require('fs').promises;

(async () => {
    // Configurazione
    const url = process.env.TARGET_URL || 'https://streamingcommunity.spa/watch/314';
    const outputFile = 'streaming.m3u8';
    const playButtonSelector = process.env.PLAY_BUTTON_SELECTOR || '#play-button';
    const networkLogFile = 'network_requests.log';
    const iframeContentFile = 'iframe_content.html';

    // Avvia il browser
    console.log('Avvio del browser Puppeteer...');
    const browser = await puppeteer.launch({
        headless: 'new',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-service-workers'
        ],
        executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium'
    });
    const page = await browser.newPage();

    // Intercetta i log della console
    page.on('console', msg => console.log('Console del browser:', msg.text()));

    // Imposta User-Agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

    // Aggiungi cookie di autenticazione (esempio, da configurare)
    /* await page.setCookie({
        name: 'session_cookie_name',
        value: 'session_cookie_value',
        domain: 'streamingcommunity.spa'
    }); */

    // Intercetta tutte le richieste di rete
    await page.setRequestInterception(true);
    const m3u8Links = new Set();
    const networkRequests = [];

    page.on('request', request => {
        const requestUrl = request.url();
        networkRequests.push(requestUrl);
        if (requestUrl.includes('.m3u8') || requestUrl.includes('vixcloud.co/playlist')) {
            console.log(`Flusso M3U8 o playlist trovato: ${requestUrl}`);
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

        // Salva il contenuto HTML completo
        const pageContent = await page.content();
        await fs.writeFile('page_content.html', pageContent);
        console.log('Contenuto HTML salvato come page_content.html');

        // Salva le richieste di rete
        await fs.writeFile(networkLogFile, networkRequests.join('\n'));
        console.log(`Richieste di rete salvate come ${networkLogFile}`);

        // Cerca iframe
        const iframes = await page.$$('iframe');
        console.log(`Iframe trovati: ${iframes.length}`);
        for (let i = 0; i < iframes.length; i++) {
            const frame = await iframes[i].contentFrame();
            if (frame) {
                const frameUrl = await frame.url();
                console.log(`Iframe ${i + 1} URL: ${frameUrl}`);
                if (frameUrl.includes('vixcloud.co')) {
                    console.log('Iframe di vixcloud.co trovato, intercetto richieste...');
                    await frame.setRequestInterception(true);
                    frame.on('request', request => {
                        const requestUrl = request.url();
                        networkRequests.push(requestUrl);
                        if (requestUrl.includes('.m3u8') || requestUrl.includes('vixcloud.co/playlist')) {
                            console.log(`Flusso M3U8 o playlist in iframe: ${requestUrl}`);
                            m3u8Links.add(requestUrl);
                        }
                        request.continue();
                    });
                    // Salva il contenuto dell'iframe
                    const frameContent = await frame.content();
                    await fs.appendFile(iframeContentFile, `Iframe ${i + 1} (${frameUrl}):\n${frameContent}\n\n`);
                    console.log(`Contenuto iframe ${i + 1} salvato in ${iframeContentFile}`);
                }
            }
        }

        // Cerca il player video
        const videoElement = await page.$('video');
        const playerClasses = await page.$$('[class*="player"], [class*="video"], [class*="play"]');
        console.log(`Elementi <video> trovati: ${videoElement ? 1 : 0}`);
        console.log(`Elementi con classi player/video/play trovati: ${playerClasses.length}`);

        // Verifica attributi del player
        if (videoElement) {
            const videoSrc = await page.evaluate(el => el.src, videoElement);
            console.log(`Attributo src del video: ${videoSrc || 'non presente'}`);
        }

        // Verifica se il pulsante play esiste
        console.log(`Verifica del selettore: ${playButtonSelector}`);
        let playButton = await page.$(playButtonSelector);
        if (playButton) {
            console.log('Pulsante play trovato, clicco...');
            await page.click(playButtonSelector);
        } else {
            console.log('Pulsante play non trovato, provo selettori alternativi...');
            const alternativeSelectors = [
                '.play-btn',
                'button.video-play',
                '[aria-label="Play"]',
                'button',
                '.vjs-play-control',
                '.vjs-big-play-button'
            ];
            for (const selector of alternativeSelectors) {
                playButton = await page.$(selector);
                if (playButton) {
                    console.log(`Trovato selettore alternativo ${selector}, clicco...`);
                    await page.click(selector);
                    break;
                }
            }
            if (!playButton) {
                console.log('Nessun selettore alternativo trovato, simulo interazioni naturali...');
                if (videoElement) {
                    await page.evaluate(el => el.click(), videoElement);
                    console.log('Cliccato sul tag <video>.');
                } else if (playerClasses.length > 0) {
                    await page.evaluate(el => el.click(), playerClasses[0]);
                    console.log('Cliccato sul primo elemento player.');
                } else {
                    console.log('Nessun player trovato, scrollo e clicco su <body>...');
                    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
                    await page.click('body');
                    console.log('Scroll e clic su <body> completati.');
                }
            }
        }

        // Aspetta 40 secondi per il caricamento del video
        console.log('Attendo 40 secondi per il caricamento del video...');
        await new Promise(resolve => setTimeout(resolve, 40000));

        // Salva i link trovati
        if (m3u8Links.size === 0) {
            console.log('Nessun flusso M3U8 trovato.');
            await fs.writeFile(outputFile, ''); // Crea un file vuoto
        } else {
            const links = Array.from(m3u8Links).join('\n');
            await fs.writeFile(outputFile, links);
            console.log(`Trovati ${m3u8Links.size} flussi M3U8. Salvati in ${outputFile}`);
            if (links.includes('vixcloud.co/playlist/253542')) {
                console.log('URL desiderato trovato e salvato!');
            }
        }

    } catch (error) {
        console.error(`Errore durante l'esecuzione: ${error.message}`);
        await page.screenshot({ path: 'error_screenshot.png', fullPage: true });
        console.log('Screenshot di errore salvato come error_screenshot.png');
        process.exit(1);
    } finally {
        await browser.close();
        console.log('Browser chiuso.');
    }
})();