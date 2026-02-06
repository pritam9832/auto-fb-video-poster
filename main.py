import os
import glob
import subprocess
import yt_dlp
import requests
import time

# ================= CONFIG =================
YOUTUBE_CHANNEL = "https://www.youtube.com/@souravjvlogs/videos"

DOWNLOAD_DIR = "downloads"
MY_VIDEO = "my_video.mp4"

PAGE_ID = "171507192718897"
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

FFMPEG = "ffmpeg"
# =========================================


def run(cmd):
    print("▶", cmd)
    subprocess.run(cmd, shell=True, check=True)


# ---------- STEP 1: DOWNLOAD LATEST YOUTUBE VIDEO ----------
def download_latest_video():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    ydl_opts = {
        "outtmpl": f"{DOWNLOAD_DIR}/vlog.%(ext)s",
        "format": "mp4",
        "playlist_items": "1",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([YOUTUBE_CHANNEL])


# ---------- STEP 2: CREATE 3 PARTS ----------
def create_parts():
    parts = [
        (0, 180, "part1.mp4"),
        (180, 360, "part2.mp4"),
        (360, 540, "part3.mp4"),
    ]

    for i, (start, end, output) in enumerate(parts, 1):
        print(f"\n🎬 Creating Part {i}")

        temp_vlog = f"temp_vlog_{i}.mp4"

        run(
            f'"{FFMPEG}" -y -ss {start} -to {end} -i "{DOWNLOAD_DIR}/vlog.mp4" '
            f'-filter:v "setpts=PTS/1.05" -filter:a "atempo=1.05" '
            f'-c:v libx264 -c:a aac "{temp_vlog}"'
        )

        run(
            f'"{FFMPEG}" -y -i "{temp_vlog}" -i "{MY_VIDEO}" '
            f'-filter_complex '
            f'"[1:v]scale=640:360:force_original_aspect_ratio=decrease,'
            f'pad=640:360:(ow-iw)/2:(oh-ih)/2,setsar=1[v1];'
            f'[0:v][0:a][v1][1:a]concat=n=2:v=1:a=1[outv][outa]" '
            f'-map "[outv]" -map "[outa]" '
            f'-c:v libx264 -c:a aac "{output}"'
        )

        os.remove(temp_vlog)


# ---------- STEP 3: UPLOAD TO FACEBOOK ----------
def upload_to_facebook(video_path, caption):
    print(f"\n⬆️ Uploading {video_path}")

 url = f"https://graph.facebook.com/v24.0/{PAGE_ID}/videos"
    params = {
        "access_token": PAGE_ACCESS_TOKEN,
        "description": caption
    }

    with open(video_path, "rb") as video:
        response = requests.post(
            url,
            params=params,
            files={"source": video}
        )

    print("RESPONSE:", response.text)
    response.raise_for_status()
    print("✅ Uploaded:", video_path)


# ---------- STEP 4: CLEANUP ----------
def cleanup():
    print("\n🧹 Cleaning local storage...")

    files = [
        f"{DOWNLOAD_DIR}/vlog.mp4",
        "part1.mp4",
        "part2.mp4",
        "part3.mp4",
    ]

    temp_files = glob.glob("temp_vlog_*.mp4")

    for file in files + temp_files:
        if os.path.exists(file):
            os.remove(file)
            print("🗑️ Deleted:", file)

    print("✅ Cleanup complete")


# ================= MAIN =================
if __name__ == "__main__":
    print("\n⬇️ Downloading latest YouTube vlog...")
    download_latest_video()

    print("\n🎬 Creating 3 video parts...")
    create_parts()

    print("\n⬆️ Uploading to Facebook Page...")
    upload_to_facebook("part1.mp4", "Sourav Joshi Vlog Today | Part 1")
    time.sleep(120)

    upload_to_facebook("part2.mp4", "Sourav Joshi Vlog Today | Part 2")
    time.sleep(120)

    upload_to_facebook("part3.mp4", "Sourav Joshi Vlog Today | Part 3")

    cleanup()

    print("\n🎉 ALL DONE — 3 PARTS UPLOADED & STORAGE CLEAN 🎉")

