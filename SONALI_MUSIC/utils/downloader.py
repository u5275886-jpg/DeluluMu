from os import path
import os
import yt_dlp
from yt_dlp.utils import DownloadError

def get_cookie_file() -> str:
    if os.path.exists("cookies/cookies.txt"):
        return "cookies/cookies.txt"
    elif os.path.exists("SONALI_MUSIC/assets/cookies.txt"):
        return "SONALI_MUSIC/assets/cookies.txt"
    return None

ytdl_opts = {
    "outtmpl": "downloads/%(id)s.%(ext)s",
    "format": "bestaudio[ext=m4a]",
    "geo_bypass": True,
    "nocheckcertificate": True,
}
cookiefile = get_cookie_file()
if cookiefile:
    ytdl_opts["cookiefile"] = cookiefile

ytdl = yt_dlp.YoutubeDL(ytdl_opts)


def download(url: str, my_hook) -> str:       
    ydl_optssx = {
        'format' : 'bestaudio[ext=m4a]',
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "geo_bypass": True,
        "nocheckcertificate": True,
        'quiet': True,
        'no_warnings': True,
    }
    if cookiefile:
        ydl_optssx["cookiefile"] = cookiefile
    info = ytdl.extract_info(url, False)
    try:
        x = yt_dlp.YoutubeDL(ydl_optssx)
        x.add_progress_hook(my_hook)
        dloader = x.download([url])
    except Exception as y_e:
        return print(y_e)
    else:
        dloader
    xyz = path.join("downloads", f"{info['id']}.{info['ext']}")
    return xyz
