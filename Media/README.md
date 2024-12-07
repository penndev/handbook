
**媒体调试工具**

- SpecialVH264 NAL分析工具
  - 源码 https://github.com/leixiaohua1020/h264_analysis
  - 下载 https://sourceforge.net/projects/h264streamanalysis/files/binary/
- YUV Player 工具 https://github.com/Tee0125/yuvplayer
- 面向开发者的视频调试工具 https://www.elecard.com/
- MPEG-TS 分析工具 https://www.easyice.cn/


**文档**

- https://www.itu.int/itu-t/recommendations/rec.aspx?rec=H.264
- https://www.itu.int/itu-t/recommendations/rec.aspx?rec=H.265


**名词说明**

- 时间冗余（帧间编码）：物体存在运动规律，同一个场景存在大量的重复背景元素。
- 空间冗余（帧内编码）：物体在图片上存在大量重复的元素。
- GOP(I->P->B-I)：Gropu of Pictures 动起来的图片就是视频。
  - Intra-coded picture 帧内编码图片。
  - Predictive-coded Picture 预测编码图片。
  - Bidirectionally predicted picture 双向预测图片。
- YCrCb: （Y-Luminance 亮度）（C Chrominance 色度）


- 色度采样率 4:2:0(j:a:b) 形容一个以J个像素宽及两个像素高的概念上区域
> 4:2:0 对数据压缩率为 8*(8*3) / 8*(8+4) 所以压缩率为一半。
  - J：水平抽样引用（概念上区域的宽度）。通常为4。
  - a：在J个像素第一行中的色度抽样数目（Cr, Cb）。
  - b：在J个像素第二行中的额外色度抽样数目（Cr, Cb）。

