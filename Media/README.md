> 视频、音频、图片分析

- [YUV采样与编码](./yuv.md)
- [JPEG](./JPEG.md)
- [H264](./H264.md)
- [MPEG2-TS分析](./MPEG2-TS.md)
- [rtmp与flv](./RTMP.md)
- [FFmpeg](./FFmpeg.md)

## 编解码官方文档

- **H264** https://www.itu.int/itu-t/recommendations/rec.aspx?rec=H.264
- **H265** https://www.itu.int/itu-t/recommendations/rec.aspx?rec=H.265

## 媒体容器文档

- 编码标准 [ISO_IEC_14496-15-AVC-format-2017.pdf](./docs/ISO_IEC_14496-15-AVC-format-2017.pdf)
- **flv** Adobe 研发，与 RTMP 搭配，是主流直播推流协议 https://veovera.org/docs/legacy/
  - 基础版本 https://veovera.github.io/enhanced-rtmp/docs/legacy/video-file-format-v10-1-spec.pdf
  - 加强版 https://veovera.org/docs/enhanced/enhanced-rtmp-v2.html

## 分析脚本

- MPEG2-TS：[`_code/media/ts.py`](../_code/media/ts.py)
- FLV：[`_code/media/flv.py`](../_code/media/flv.py)
- H264：[`_code/h26x/h264.py`](../_code/h26x/h264.py)

## 分析工具

- SpecialVH264 NAL 分析工具
  - 源码 https://github.com/leixiaohua1020/h264_analysis
  - 下载 https://sourceforge.net/projects/h264streamanalysis/files/binary/
- YUV Player 工具 https://github.com/Tee0125/yuvplayer
- 面向开发者的视频调试工具 https://www.elecard.com/
- MPEG-TS 分析工具 https://www.easyice.cn/

## 名词说明

- 时间冗余（帧间编码）
  - 运动预测：物体在影像展示中普遍符合物理运动规律，比如一个球从 $(X_1,Y_1)$ 运动到 $(X_1,Y_5)$ 的位置，我们可以只编码这个物体的运动距离即可。
  - 当前帧与上一帧除了球的运动其他都没有变动，存在背景冗余。
- 空间冗余（帧内编码）：物体在图片上存在大量重复的元素，比如一个黑色的正方形，大部分区域在颜色表达上基本一致。
- GOP（I→P→B→I）：Group of Pictures，动起来的图片就是视频。
  - I 帧（Intra-coded）：完整画面，不参考其他帧即可解码
  - P 帧（Predictive-coded）：前向参考，需要参考前面的帧
  - B 帧（Bidirectionally predicted）：双向参考，需要前后帧
  - SP 帧（Switching P Picture）
  - SI 帧（Switching I Picture）
