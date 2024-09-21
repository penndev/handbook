

# FFmpeg

- 官网 https://www.ffmpeg.org/


## 常用命令

 简单转换单个文件格式

    > ffmpeg -i input.mp4 -vcodec libx264 -acodec aac output.mp4

- `-vcodec (-c:v)` 指定视频编码器(-c:v)简写
- `-acodec (-c:a)` 指定视频编码器(-c:a)简写
- `-ss` 指定开始时间  00:00:00

ffmpeg -i input.mp4  -vframes 1 output.mp4