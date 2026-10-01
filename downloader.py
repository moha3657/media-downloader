import yt_dlp
import os

DOWNLOAD_DIR = r'C:\Users\SAMA\Downloads\%(title)s.%(ext)s'

def run_downloader():
    url = input("\nEnter YouTube / Shorts URL: ").strip()
    if not url:
        print("Invalid URL.")
        return

    print("\nSelect Download Option:")
    print("[1] Best Video Quality (Auto Merge via FFmpeg)")
    print("[2] Audio Only (MP3)")
    print("[3] Select Specific Resolution (Deduplicated)")
    
    choice = input("\nEnter choice (1-3): ").strip()

    if choice == '1':
        ydl_opts = {
            'outtmpl': DOWNLOAD_DIR,
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        }
    elif choice == '2':
        ydl_opts = {
            'outtmpl': DOWNLOAD_DIR,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    elif choice == '3':
        info_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            print("\nAnalyzing available formats...")
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            print(f"\nTitle: {info.get('title')}")
            print("-" * 45)
            
            unique_resolutions = {}

            for f in formats:
                vcodec = f.get('vcodec', 'none')
                height = f.get('height')
                f_id = f.get('format_id')

                if vcodec != 'none' and height:
                    if height not in unique_resolutions:
                        unique_resolutions[height] = f_id

            sorted_heights = sorted(unique_resolutions.keys(), reverse=True)
            
            options_list = []
            count = 1

            print("\n--- Video Options ---")
            for res in sorted_heights:
                note = f"Video MP4 | Quality: {res}p"
                target_format = f"bestvideo[height<={res}]+bestaudio/best[height<={res}]"
                options_list.append(target_format)
                print(f"[{count}] - {note}")
                count += 1

            print("\n--- Audio Options ---")
            options_list.append("bestaudio")
            print(f"[{count}] - Audio Only (Best Quality MP3)")

            selected = int(input("\nEnter option number: ")) - 1
            chosen_format = options_list[selected]

            ydl_opts = {
                'outtmpl': DOWNLOAD_DIR,
                'format': chosen_format,
                'merge_output_format': 'mp4',
            }

            if chosen_format == "bestaudio":
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]

    else:
        print("Invalid option selected.")
        return

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("\nDownloading and processing with FFmpeg...")
            ydl.download([url])
            print("\nDownload complete! File saved to Downloads directory.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == '__main__':
    run_downloader()