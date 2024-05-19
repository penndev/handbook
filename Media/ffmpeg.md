

## ffmpeg

### 简单转换单个文件格式

    > ffmpeg -i input.mp4 -vcodec libx264 -acodec aac output.mp4

- `-vcodec (-c:v)` 指定视频编码器(-c:v)简写
- `-acodec (-c:a)` 指定视频编码器(-c:a)简写


### 分割文件
```
ffmpeg -i input.mp4 -c copy -segment_time 15        -f segment output_%03d.mp4
ffmpeg -i input.mp4 -c copy -map 0 -segment_time 10 -f segment output_%03d.mp4
```


### MP4转M3U8
```bash
ffmpeg -i in.mp4 -vcodec libx264 -acodec aac -hls_list_size 0 -hls_time 30 -hls_enc 1 -hls_enc_key 0123456789abcdef out.m3u8
```


### 已经编译后的静态文件

https://johnvansickle.com/ffmpeg/
