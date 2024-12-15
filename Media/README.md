
**媒体调试工具**

- SpecialVH264 NAL分析工具
  - 源码 https://github.com/leixiaohua1020/h264_analysis
  - 下载 https://sourceforge.net/projects/h264streamanalysis/files/binary/
- YUV Player 工具 https://github.com/Tee0125/yuvplayer
- 面向开发者的视频调试工具 https://www.elecard.com/
- MPEG-TS 分析工具 https://www.easyice.cn/


**编解码文档**

- **H264** https://www.itu.int/itu-t/recommendations/rec.aspx?rec=H.264
- **H265** https://www.itu.int/itu-t/recommendations/rec.aspx?rec=H.265


**名词说明**

- 时间冗余（帧间编码）
  - 运动预测 物体在影像展示中普遍符合物理运动规律，比如一个球在 $X_1$,$Y_1$ 运动到 $X_1$,$Y_5$ 的位置，我们可以只编码这个物体的运动距离即可。
  - 当前帧与上一帧除了球的运动其他都没有变动，存在背景冗余。

- 空间冗余（帧内编码）：物体在图片上存在大量重复的元素,比如一个黑色的正方形，大部分区域在颜色表达上基本一致。

- GOP (I->P->B-I)：Group of Pictures 动起来的图片就是视频。
  - Intra-coded picture 帧内编码图片。
  - Predictive-coded Picture 预测编码图片。
  - Bidirectionally predicted picture 双向预测图片。

176 144