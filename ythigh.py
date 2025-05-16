from yt_dlp import YoutubeDL
import subprocess
import os

def find_and_combine_m3u8(url, output_dir="output", m3u8_filename="highlights.m3u8"):
    ydl_opts = {
        'quiet': True,
        'simulate': True,
    }

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        
        video_format = None
        audio_format = None
        
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
        
        # File MP4 temporaneo
        temp_file = f"{output_dir}/temp_output.mp4"
        m3u8_output = f"{output_dir}/{m3u8_filename}"
        
        # Scarica i flussi combinati con yt-dlp
        ydl_opts_download = {
            'format': f"{video_format['format_id']}+{audio_format['format_id']}",
            'outtmpl': temp_file,
            'merge_output_format': 'mp4',
        }
        
        with YoutubeDL(ydl_opts_download) as ydl:
            ydl.download([url])
            print(f"File MP4 temporaneo generato: {temp_file}")
        
        # Converti in m3u8 con FFmpeg
        ffmpeg_command = [
            'ffmpeg', '-i', temp_file,
            '-c:v', 'copy', '-c:a', 'copy',
            '-f', 'hls',
            '-hls_time', '10',
            '-hls_list_size', '0',
            '-hls_segment_filename', f"{output_dir}/highlights_%03d.ts",
            m3u8_output
        ]
        
        try:
            subprocess.run(ffmpeg_command, check=True)
            print(f"File m3u8 generato: {m3u8_output}")
            # Rimuovi il file MP4 temporaneo
            os.remove(temp_file)
            print(f"File MP4 temporaneo rimosso: {temp_file}")
        except subprocess.CalledProcessError as e:
            print(f"Errore nella creazione del file m3u8: {e}")
        except FileNotFoundError:
            print("Errore: FFmpeg non trovato.")

if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=pOubWv5h0lc"
    find_and_combine_m3u8(url)
