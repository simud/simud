const puppeteer = require('puppeteer');
const fs = require('fs').promises;

(async () => {
    // Versione dello script
    console.log('Script Versione: 1.16 - Navigazione diretta all\'iframe');

    // Configurazione
    const url = 'https://streamingcommunity.spa/iframe/314'; // Navigazione diretta all'iframe
    const outputFile = 'streaming.m3u8';
    const playButtonSelector = process.env.PLAY_BUTTON_SELECTOR || '#play-button';
    const networkLogFile = 'network_requests.log';
    const iframeContentFile = 'iframe_content.html';
    const sessionCookie = process.env.SESSION_COOKIE || ''; // Cookie di autenticazione

    // Verifica presenza del cookie
    if (!sessionCookie) {
        console.error('Errore: Nessun cookie di autenticazione fornito. Il cookie è obbligatorio per accedere al flusso. Imposta la variabile d\'ambiente SESSION_COOKIE.');
        process.exit(1);
    }

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

    // Aggiungi cookie di autenticazione
    await page.setCookie({
        name: 'session',
        value: sessionCookie,
        domain: 'streamingcommunity.spa'
    });
    console.log('Cookie di autenticazione aggiunto.');

    // Disabilita il Service Worker e applica override
    await page.evaluateOnNewDocument(() => {
        // Disabilita Service Worker
        navigator.serviceWorker.getRegistrations().then(registrations => {
            for (let registration of registrations) {
                registration.unregister();
            }
        });
        Object.defineProperty(navigator, 'serviceWorker', {
            value: undefined,
            writable: false
        });

        // Funzione per applicare gli override
        window.applyOverrides = () => {
            // Override HLS.js
            Object.defineProperty(window, 'Hls', {
                configurable: true,
                set: function (value) {
                    if (value && value.isSupported) {
                        const originalLoadSource = value.prototype.loadSource;
                        value.prototype.loadSource = function (url) {
                            console.log('HLS.js loadSource intercettato:', url);
                            window.hlsStreamUrl = url;
                            return originalLoadSource.apply(this, arguments);
                        };
                    }
                    this._Hls = value;
                },
                get: function () {
                    return this._Hls;
                }
            });

            // Intercetta XHR
            const originalXHROpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function () {
                const url = arguments[1];
                console.log('XHR aperto:', url);
                if (url.includes('vixcloud.co/playlist')) {
                    console.log('XHR intercettato:', url);
                    window.xhrStreamUrl = url;
                }
                return originalXHROpen.apply(this, arguments);
            };

            // Intercetta Fetch
            const originalFetch = window.fetch;
            window.fetch = async function () {
                const url = arguments[0].url || arguments[0];
                console.log('Fetch avviato:', url);
                if (typeof url === 'string' && url.includes('vixcloud.co/playlist')) {
                    console.log('Fetch intercettato:', url);
                    window.fetchStreamUrl = url;
                }
                return originalFetch.apply(this, arguments);
            };

            // Intercetta Web Worker
            const originalWorker = window.Worker;
            window.Worker = function (url) {
                console.log('Web Worker rilevato:', url);
                const worker = new originalWorker(url);
                worker.onmessage = function (event) {
                    console.log('Messaggio ricevuto dal worker:', event.data);
                    if (typeof event.data === 'string' && event.data.includes('vixcloud.co/playlist')) {
                        window.workerStreamUrl = event.data;
                    }
                };
                return worker;
            };

            // Intercetta eventi video
            const originalVideoPlay = HTMLVideoElement.prototype.play;
            HTMLVideoElement.prototype.play = function () {
                console.log('Video play intercettato');
                this.addEventListener('loadedmetadata', () => {
                    console.log('Evento loadedmetadata: src=', this.src);
                    if (this.src.includes('vixcloud.co/playlist')) {
                        window.videoStreamUrl = this.src;
                    }
                });
                this.addEventListener('error', (e) => {
                    console.log('Errore video:', e);
                });
                return originalVideoPlay.apply(this, arguments);
            };
        };

        // Applica gli override nella pagina principale
        window.applyOverrides();
    });

    // Intercetta tutte le richieste di rete
    await page.setRequestInterception(true);
    const streamLinks = new Set();
    const networkRequests = [];

    page.on('request', request => {
        const requestUrl = request.url();
        networkRequests.push(requestUrl);
        if (requestUrl.includes('vixcloud.co')) {
            console.log(`Richiesta rilevata con vixcloud.co: ${requestUrl}`);
        }
        if (requestUrl.includes('vixcloud.co/playlist')) {
            console.log(`Flusso trovato: ${requestUrl}`);
            streamLinks.add(requestUrl);
        }
        request.continue();
    });

    // Intercetta le risposte per cercare flussi
    page.on('response', async response => {
        const responseUrl = response.url();
        if (responseUrl.includes('vixcloud.co')) {
            console.log(`Risposta rilevata con vixcloud.co: ${responseUrl}`);
        }
        if (responseUrl.includes('vixcloud.co/playlist')) {
            console.log(`Flusso trovato nella risposta: ${responseUrl}`);
            streamLinks.add(responseUrl);
        }
    });

    try {
        // Naviga direttamente all'iframe
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

        // Cerca iframe annidati
        const iframes = await page.$$('iframe');
        console.log(`Iframe trovati: ${iframes.length}`);
        for (let i = 0; i < iframes.length; i++) {
            const frame = await iframes[i].contentFrame();
            if (frame) {
                const frameUrl = await frame.url();
                console.log(`Iframe ${i + 1} URL: ${frameUrl}`);
                const frameContent = await frame.content();
                await fs.appendFile(iframeContentFile, `Iframe ${i + 1} (${frameUrl}):\n${frameContent}\n\n`);
                console.log(`Contenuto iframe ${i + 1} salvato in ${iframeContentFile}`);
                // Applica override nell'iframe
                try {
                    await frame.evaluate(() => {
                        window.applyOverrides && window.applyOverrides();
                    });
                } catch (e) {
                    console.log(`Errore applicazione override in iframe ${i + 1}:`, e.message);
                }
                // Cerca il player nell'iframe
                const nestedVideo = await frame.$('video');
                const nestedPlayerClasses = await frame.$$('[class*="player"], [class*="video"], [class*="play"]');
                console.log(`Elementi <video> trovati in iframe ${i + 1}: ${nestedVideo ? 1 : 0}`);
                console.log(`Elementi con classi player/video/play trovati in iframe ${i + 1}: ${nestedPlayerClasses.length}`);
                if (nestedPlayerClasses.length > 0) {
                    await frame.evaluate(el => el.click(), nestedPlayerClasses[0]);
                    console.log(`Cliccato sul primo elemento player in iframe ${i + 1}.`);

                    // Tenta di estrarre il flusso
                    const streamUrl = await frame.evaluate(() => {
                        return new Promise((resolve) => {
                            const video = document.querySelector('video');
                            if (video && window.Hls && window.Hls.isSupported()) {
                                const hls = new window.Hls();
                                hls.attachMedia(video);
                                hls.on(window.Hls.Events.MANIFEST_LOADED, (event, data) => {
                                    console.log('HLS.js manifesto caricato:', data.url);
                                    resolve(data.url || null);
                                });
                                hls.on(window.Hls.Events.MEDIA_ATTACHED, () => {
                                    console.log('HLS.js media attaccato');
                                });
                                hls.on(window.Hls.Events.ERROR, (event, data) => {
                                    console.log('Errore HLS.js:', data);
                                    resolve(null);
                                });
                                // Avvia il video
                                video.play().catch(err => {
                                    console.log('Errore avvio video:', err);
                                    resolve(null);
                                });
                                // Controlla se l'URL è stato intercettato
                                setInterval(() => {
                                    if (window.hlsStreamUrl) {
                                        resolve(window.hlsStreamUrl);
                                    } else if (window.xhrStreamUrl) {
                                        resolve(window.xhrStreamUrl);
                                    } else if (window.fetchStreamUrl) {
                                        resolve(window.fetchStreamUrl);
                                    } else if (window.workerStreamUrl) {
                                        resolve(window.workerStreamUrl);
                                    } else if (window.videoStreamUrl) {
                                        resolve(window.videoStreamUrl);
                                    }
                                }, 1000);
                                // Timeout di sicurezza
                                setTimeout(() => resolve(null), 10000);
                            } else {
                                resolve(null);
                            }
                        });
                    });
                    if (streamUrl) {
                        console.log(`Flusso trovato: ${streamUrl}`);
                        streamLinks.add(streamUrl);
                    }

                    // Controllo alternativo: cerca attributi dati o src nel video
                    const videoData = await frame.evaluate(() => {
                        const video = document.querySelector('video');
                        if (video) {
                            const src = video.src || video.getAttribute('data-src') || video.getAttribute('data-hls') || null;
                            return src;
                        }
                        return null;
                    });
                    if (videoData) {
                        console.log(`Attributo src/data del video in iframe ${i + 1}: ${videoData}`);
                        if (videoData.includes('vixcloud.co/playlist')) {
                            console.log(`Flusso trovato tramite attributi video: ${videoData}`);
                            streamLinks.add(videoData);
                        }
                    }
                } else if (nestedVideo) {
                    const videoSrc = await frame.evaluate(el => el.src, nestedVideo);
                    console.log(`Attributo src del video in iframe ${i + 1}: ${videoSrc || 'non presente'}`);
                    await frame.evaluate(el => el.click(), nestedVideo);
                    console.log(`Cliccato sul tag <video> in iframe ${i + 1}.`);
                } else if (frameUrl.includes('vixcloud.co/embed/253542')) {
                    console.log('Iframe di Vixcloud trovato, simulo clic al centro...');
                    await frame.evaluate(() => {
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

        // Aspetta 90 secondi per il caricamento del video
        console.log('Attendo 90 secondi per il caricamento del video...');
        await new Promise(resolve => setTimeout(resolve, 90000));

        // Salva i link trovati
        if (streamLinks.size === 0) {
            console.log('Nessun flusso trovato.');
            await fs.writeFile(outputFile, '');
        } else {
            const links = Array.from(streamLinks).join('\n');
            await fs.writeFile(outputFile, links);
            console.log(`Trovati ${streamLinks.size} flussi. Salvati in ${outputFile}`);
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