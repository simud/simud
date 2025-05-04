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
            '--disable-service-workers',
            '--disable-background-networking',
            '--disable-features=ServiceWorker,NetworkService'
        ],
        executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
        protocolTimeout: 120000 // Timeout di 120 secondi
    });
    const page = await browser.newPage();

    // Intercetta i log della console
    page.on('console', msg => console.log('Console del browser:', msg.text()));

    // Imposta User-Agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

    // Disabilita il Service Worker
    await page.evaluateOnNewDocument(() => {
        navigator.serviceWorker.getRegistrations().then(registrations => {
            for (let registration of registrations) {
                registration.unregister();
            }
        });
    });

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
        await page.screenshot({ path: 'debug_screenshot.png' });
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
                // Salva il contenuto dell'iframe
                const frameContent = await frame.content();
                await fs.appendFile(iframeContentFile, `Iframe ${i + 1} (${frameUrl}):\n${frameContent}\n\n`);
                console.log(`Contenuto iframe ${i + 1} salvato in ${iframeContentFile}`);
                // Cerca iframe annidati
                const nestedIframes = await frame.$$('iframe');
                console.log(`Iframe annidati in iframe ${i + 1}: ${nestedIframes.length}`);
                for (let j = 0; j < nestedIframes.length; j++) {
                    const nestedFrame = await nestedIframes[j].contentFrame();
                    if (nestedFrame) {
                        const nestedFrameUrl = await nestedFrame.url();
                        console.log(`Iframe annidato ${j + 1} URL: ${nestedFrameUrl}`);
                        const nestedFrameContent = await nestedFrame.content();
                        await fs.appendFile(iframeContentFile, `Iframe annidato ${j + 1} (${nestedFrameUrl}):\n${nestedFrameContent}\n\n`);
                        // Cerca il player nell'iframe annidato
                        const nestedVideo = await nestedFrame.$('video');
                        const nestedPlayerClasses = await nestedFrame.$$('[class*="player"], [class*="video"], [class*="play"]');
                        console.log(`Elementi <video> trovati in iframe annidato ${j + 1}: ${nestedVideo ? 1 : 0}`);
                        console.log(`Elementi con classi player/video/play trovati in iframe annidato ${j + 1}: ${nestedPlayerClasses.length}`);
                        if (nestedVideo) {
                            const videoSrc = await nestedFrame.evaluate(el => el.src, nestedVideo);
                            console.log(`Attributo src del video in iframe annidato ${j + 1}: ${videoSrc || 'non presente'}`);
                            await nestedFrame.evaluate(el => el.click(), nestedVideo);
                            console.log(`Cliccato sul tag <video> in iframe annidato ${j + 1}.`);
                        } else if (nestedPlayerClasses.length > 0) {
                            await nestedFrame.evaluate(el => el.click(), nestedPlayerClasses[0]);
                            console.log(`Cliccato sul primo elemento player in iframe annidato ${j + 1}.`);
                        } else if (nestedFrameUrl.includes('vixcloud.co/embed/253542')) {
                            console.log('Iframe di Vixcloud trovato, simulo clic al centro...');
                            await nestedFrame.evaluate(() => {
                                const x = window.innerWidth / 2;
                                const y = window.innerHeight / 2;
                                const clickEvent = new MouseEvent('click', {
                                    view: window,
                                    bubbles: true,
                                    cancelable: true,
                                    clientX: x,
                                    clientY: y
                                });
                                document.elementFromPoint(x, y).dispatchEvent(clickEvent);
                            });
                        }
                    }
                }
                // Cerca il player nell'iframe principale
                const frameVideo = await frame.$('video');
                const framePlayerClasses = await frame.$$('[class*="player"], [class*="video"], [class*="play"]');
                console.log(`Elementi <video> trovati in iframe ${i + 1}: ${frameVideo ? 1 : 0}`);
                console.log(`Elementi con classi player/video/play trovati in iframe ${i + 1}: ${framePlayerClasses.length}`);
                if (frameVideo) {
                    const videoSrc = await frame.evaluate(el => el.src, frameVideo);
                    console.log(`Attributo src del video in iframe ${i + 1}: ${videoSrc || 'non presente'}`);
                    await frame.evaluate(el => el.click(), frameVideo);
                    console.log(`Cliccato sul tag <video> in iframe ${i + 1}.`);
                } else if (framePlayerClasses.length > 0) {
                    await frame.evaluate(el => el.click(), framePlayerClasses[0]);
                    console.log(`Cliccato sul primo elemento player in iframe ${i + 1}.`);
                }
            }
        }

        // Cerca il player video nella pagina principale
        const videoElement = await page.$('video');
        const playerClasses = await page.$$('[class*="player"], [class*="video"], [class*="play"]');
        console.log(`Elementi <video> trovati nella pagina principale: ${videoElement ? 1 : 0}`);
        console.log(`Elementi con classi player/video/play trovati nella pagina principale: ${playerClasses.length}`);

        // Verifica attributi del player
        if (videoElement) {
            const videoSrc = await page.evaluate(el => el.src, videoElement);
            console.log(`Attributo src del video nella pagina principale: ${videoSrc || 'non presente'}`);
        }

        // Aspetta 40 secondi per il caricamento del video
        console.log('Attendo 40 secondi per il caricamento del video...');
        await new Promise(resolve => setTimeout(resolve, 40000));

        // Salva i link trovati
        if (m3u8Links.size === 0) {
            console.log('Nessun flusso M3U8 trovato.');
            await fs.writeFile(outputFile, '');
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