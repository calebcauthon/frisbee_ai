from types import SimpleNamespace

def get_videos():
    return [
        SimpleNamespace(
            full_path="/static/video_sources/womens_goalty_10.mp4",
            filename="womens_goalty_10.mp4",
            bytes=1024,
            length=3000,
            width=1920,
            height=1080
        ),
        SimpleNamespace(
            full_path="/static/video_sources/another_video.mp4",
            filename="another_video.mp4",
            bytes=2048,
            length=1000,
            width=1920,
            height=720
        )
    ]