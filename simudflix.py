import m3u8
import requests
import subprocess

# Funzione per scaricare un flusso m3u8
def download_m3u8_stream(url):
    # Scarica il file m3u8
    response = requests.get(url)
    m3u8_obj = m3u8.loads(response.text)

    # Prendi il primo segmento del flusso
    segment_url = m3u8_obj.segments[0].uri
    print(f"Segment URL: {segment_url}")
    
    # Se il flusso è composto da più segmenti, puoi usare ffmpeg per unirli
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', segment_url,  # URL del segmento m3u8
        '-c', 'copy',        # Copia senza ricodifica
        '-bsf:a', 'aac_adtstoasc',  # Correzione del formato audio
        'output.mp4'         # Nome del file finale
    ]
    subprocess.run(ffmpeg_cmd)

# Esegui la funzione passando l'URL del flusso m3u8
download_m3u8_stream('URL_DEL_TUO_FLUSSO_M3U8')