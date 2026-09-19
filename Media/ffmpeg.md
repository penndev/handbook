

# FFmpeg

- 官网 https://www.ffmpeg.org/


## 常用命令

 简单转换单个文件格式

    > ffmpeg -i input.mp4 -vcodec libx264 -acodec aac output.mp4

- `-vcodec (-c:v)` 指定视频编码器(-c:v)简写
- `-acodec (-c:a)` 指定视频编码器(-c:a)简写
- `-ss` 指定开始时间  00:00:00

ffmpeg -i input.mp4  -vframes 1 output.mp4

## 拆分与封装

抽出裸流后再按原编码封装回去：

```bash
ffmpeg -i .\i.mp4 out.h264
ffmpeg -i .\i.mp4 out.aac
ffmpeg -i out.h264 -i out.aac -c:v copy -c:a copy output.mp4
```