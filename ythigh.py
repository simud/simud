from yt_dlp import YoutubeDL
import subprocess
import os

def find_and_combine_m3u8(url, output_dir="output"):
    ydl_opts = {
        'quiet': True,
        'simulate': True,
    }

    # Crea la directory di output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Trova i flussi m3u8
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        
        video_format = None
        audio_format = None
        
        # Cerca flusso video 1080p e flusso audio
        for f in formats:
            if 'm3u8' in f.get('url', '') or f.get('protocol') == 'm3u8':
                if f.get('vcodec') != 'none' and f.get('height') == 1080 and not video_format:
                    video_format = f
                if f.get('acodec') != 'none' and not audio_format:
                    audio_format = f
        
        if not video_format or not audio_format:
            print("Errore: Flusso video 1080p o audio non trovato.")
            return
        
        print(f"Flusso video 1080p trovato: {video_format['url']} (Formato: {video_format['format_id']})")
        print(f"Flusso audio trovato: {audio_format['url']} (Formato: {audio_format['format_id']})")
        
        # Sostituisci caratteri non validi nel titolo
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in info['title'])
        output_file = f"{output_dir}/{safe_title}.mp4"
        m3u8_output = f"{output_dir}/{safe_title}.m3u8"
        
        # Scarica i flussi combinati con yt-dlp
        ydl_opts_download = {
            'format': f"{video_format['format_id']}+{audio_format['format_id']}",
            'outtmpl': output_file,
            'merge_output_format': 'mp4',
        }
        
        with YoutubeDL(ydl_opts_download) as ydl:
            ydl.download([url])
            print(f"File MP4 generato: {output_file}")
        
        # Converti in m3u8 con FFmpeg
        ffmpeg_command = [
            'ffmpeg', '-i', output_file,
            '-c:v', 'copy', '-c:a', 'copy',
            '-f', 'hls',
            '-hls_time', '10',
            '-hls_list_size', '0',
            '-hls_segment_filename', f"{output_dir}/{safe_title}_%03d.ts",
            m3u8_output
        ]
        
        try:
            subprocess.run(ffmpeg_command, check=True)
            print(f"File m3u8 generato: {m3u8_output}")
        except subprocess.CalledProcessError as e:
            print(f"Errore nella creazione del file m3u8: {e}")
        except FileNotFoundError:
            print("Errore: FFmpeg non trovato.")

# Esegui per il tuo video
url = "https://www.youtube.com/watch?v=pOubWv5h0lc"
find_and_combine_m3u8(url)
