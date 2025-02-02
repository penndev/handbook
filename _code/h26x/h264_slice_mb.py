from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from h264_slice_data import SliceData

from h264_define import ChromaType, Intra4x4PredMode, MbPredMode, SliceType
from h264_bs import BitStream

from h264_util import Clip3, InverseRasterScan



class MacroBlock():

    def get_coded_block_flag(self):
        # //9.3.3.1.1.9  ctxIdxInc
        '''Table 9-11'''
        if pps.entropy_coding_mode_flag != 1:
            raise ("get_mb_type pps.entropy_coding_mode_flag != 1")
        if self.slice.slice_type != SliceType.I:
            raise ('transform_size_8x8_flag != SliceType.I')
        pass

    def residual_block_cabac(self, coeffLevel, startIdx, endIdx, maxNumCoeff):
        raise ("residual_block_cabac")

    def __init__(self, bs: BitStream, slice: SliceData, ):
        '''
            **处理宏块数据**
            > 什么是宏块。
        '''
        self.slice = slice
        self.bs = bs

        slice.macroblock[slice.CurrMbAddr] = self

        self.CurrMbAddr = slice.CurrMbAddr

        self.luma4x4BlkIdx = 0 # 4x4块索引 其他类需要引用判断当前索引位置
        self.luma4x4BlkIdxTotalCoeff = {} # 保存全局状态，让他们引用
        
        self.iCbCr = None
        self.chroma4x4BlkIdx = 0
        self.chroma4x4BlkIdxTotalCoeff = {}


        self.mb_type = bs.mb_type(slice)
        self.transform_size_8x8_flag = 0
        if self.mb_type.name == "I_PCM":
            raise ("I_PCM 不经过预测，变换，量化, 直接解码")
        else:
            noSubMbPartSizeLessThan8x8Flag = 1
            if self.mb_type.name != "I_NxN" and self.mb_type.MbPartPredMode == 'Intra_16x16' and self.mb_type.NumMbPart == 4:
                raise ("子宏块分割未实现")
            else:
                if bs.pps.transform_8x8_mode_flag == 1 and  self.mb_type.name == "I_NxN":
                    self.transform_size_8x8_flag = bs.transform_size_8x8_flag()
                    if self.transform_size_8x8_flag == 1:
                        self.mb_type.MbPartPredMode = "Intra_8x8"
                self.mb_pred(bs, slice)

            self.CodedBlockPatternLuma = self.mb_type.CodedBlockPatternLuma
            self.CodedBlockPatternChroma = self.mb_type.CodedBlockPatternChroma

            if self.mb_type.MbPartPredMode != 'Intra_16x16':
                self.coded_block_pattern = bs.coded_block_pattern(slice, self)
                self.CodedBlockPatternLuma = self.coded_block_pattern % 16
                self.CodedBlockPatternChroma = self.coded_block_pattern // 16
                if self.CodedBlockPatternLuma > 0 and \
                        bs.pps.transform_8x8_mode_flag and \
                        self.mb_type.name != "I_NxN" and \
                        noSubMbPartSizeLessThan8x8Flag and \
                        (self.mb_type.name != "B_Direct_16x16" or bs.pps.direct_8x8_inference_flag):
                    self.transform_size_8x8_flag = bs.transform_size_8x8_flag()
            if self.CodedBlockPatternLuma > 0 or self.CodedBlockPatternChroma > 0 or self.mb_type.MbPartPredMode == "Intra_16x16":
                self.mb_qp_delta = bs.mb_qp_delta(slice)
                self.residual(0, 15, bs, slice)

    def mb_pred(self, bs: BitStream, slice: SliceData):
        if self.mb_type.MbPartPredMode in ("Intra_4x4", "Intra_8x8", "Intra_16x16"):
            if self.mb_type.MbPartPredMode == "Intra_4x4":
                self.prev_intra4x4_pred_mode_flag = {}
                self.rem_intra4x4_pred_mode = {}
                for luma4x4BlkIdx in range(16):
                    self.prev_intra4x4_pred_mode_flag[luma4x4BlkIdx] = bs.cabac_decode(False, ctxIdx=68) if bs.pps.entropy_coding_mode_flag else bs.read_bits(1)
                    if not self.prev_intra4x4_pred_mode_flag[luma4x4BlkIdx]:
                        self.rem_intra4x4_pred_mode[luma4x4BlkIdx] = bs.cabac_decode(False, ctxIdx=69) if bs.pps.entropy_coding_mode_flag else bs.read_bits(3)
            if self.mb_type.MbPartPredMode == "Intra_8x8":
                if slice.header.slice_type == SliceType.SI:
                    raise ("Table 9-11 mb_pred prev_intra8x8_pred_mode_flag no")
                self.prev_intra8x8_pred_mode_flag = {}
                self.rem_intra8x8_pred_mode = {}
                for luma8x8BlkIdx in range(4):
                    self.prev_intra8x8_pred_mode_flag[luma8x8BlkIdx] = bs.cabac_decode(False, ctxIdx=68) if bs.pps.entropy_coding_mode_flag else  bs.read_bits(1)
                    if not self.prev_intra8x8_pred_mode_flag[luma8x8BlkIdx]:
                        self.rem_intra8x8_pred_mode[luma8x8BlkIdx] = bs.cabac_decode(False, ctxIdx=69) if bs.pps.entropy_coding_mode_flag else  bs.read_bits(3)
            if bs.sps.chroma_format_idc in (1, 2):
                self.intra_chroma_pred_mode = bs.intra_chroma_pred_mode(slice)
        elif self.mb_type.MbPartPredMode != "Direct":
            raise ("self.mb_type.MbPartPredMode != Direct")

    def residual_block_cavlc(self, coeffLevel, startIdx, endIdx, maxNumCoeff, residualLevel:str, bs:BitStream, slice:SliceData):
        '''
            @param coeffLevel: 变换系数用于解析的作用说明
        '''
        if not coeffLevel:
            coeffLevel = {}

        TrailingOnes, TotalCoeff = bs.get_coeff(residualLevel, self, slice)

        if residualLevel in ("Intra16x16DCLevel", "Intra16x16ACLevel", "LumaLevel4x4"):
            self.luma4x4BlkIdxTotalCoeff[self.luma4x4BlkIdx] = TotalCoeff        
        if self.iCbCr != None:
            self.chroma4x4BlkIdxTotalCoeff[self.iCbCr][self.chroma4x4BlkIdx] = TotalCoeff

        if TotalCoeff > 0:
            if TotalCoeff > 10 and TrailingOnes < 3:
                suffixLength = 1
            else:
                suffixLength = 0
            levelVal = {}
            for i in range(TotalCoeff):
                if i < TrailingOnes:
                    trailing_ones_sign_flag = bs.read_bits(1)
                    levelVal[i] = 1 - 2 * trailing_ones_sign_flag
                else:
                    leading_zero_bits = -1
                    while True:
                        leading_zero_bits += 1
                        b = bs.read_bits(1)
                        if b == 1:
                            break
                    level_prefix = leading_zero_bits
                    levelCode = min(15, level_prefix) << suffixLength

                    if level_prefix == 14 and suffixLength == 0:
                        levelSuffixSize = 4
                    elif level_prefix >= 15:
                        levelSuffixSize = level_prefix - 3
                    else:
                        levelSuffixSize = suffixLength

                    if suffixLength > 0 or level_prefix >= 14:
                        if levelSuffixSize > 0:
                            level_suffix = bs.read_bits(levelSuffixSize)
                        else:
                            level_suffix = 0
                        levelCode += level_suffix

                    if level_prefix >= 15 and suffixLength == 0:
                        levelCode += 15
                    if level_prefix >= 16:
                        levelCode += (1 << (level_prefix - 3)) - 4096
                    if i == TrailingOnes and TrailingOnes < 3:
                        levelCode += 2
                    if levelCode % 2 == 0:
                        levelVal[i] = (levelCode + 2) >> 1
                    else:
                        levelVal[i] = (-levelCode - 1) >> 1
                    if suffixLength == 0:
                        suffixLength = 1
                    if abs(levelVal[i]) > (3 << (suffixLength - 1)) and suffixLength < 6:
                        suffixLength += 1

            TotalZeros = 0
            if TotalCoeff < endIdx - startIdx + 1:
                TotalZeros = bs.get_total_zeros(TotalCoeff - 1, maxNumCoeff)
            else:
                TotalZeros = 0

            runVal = {}
            zerosLeft = TotalZeros
            for i in range(TotalCoeff - 1):
                if zerosLeft > 0: 
                    runbeforeVlcIdx = zerosLeft - 1 if zerosLeft <= 6 else 6
                    runVal[i] = bs.get_runbefore( runbeforeVlcIdx) 
                else:
                    runVal[i] = 0
                zerosLeft -= runVal[i]

            runVal[TotalCoeff - 1] = zerosLeft
            coeffNum = -1
            for i in range(TotalCoeff - 1, -1, -1):
                coeffNum += runVal[i] + 1
                coeffLevel[startIdx + coeffNum] = levelVal[i]
        return coeffLevel
    
    def residual(self, startIdx, endIdx, bs: BitStream, slice: SliceData):
        if bs.pps.entropy_coding_mode_flag != 1:
            self.residual_block = self.residual_block_cavlc
        else:
            self.residual_block = self.residual_block_cabac

        Intra16x16DCLevel, Intra16x16ACLevel, LumaLevel4x4, LumaLevel8x8 = self.residual_luma(
            i16x16DClevel={},
            i16x16AClevel={},
            level4x4={},
            level8x8={},
            startIdx=startIdx,
            endIdx=endIdx,

            bs=bs,
            slice=slice
        )

        ChromaDCLevel = {}
        ChromaACLevel = {}
        if bs.sps.chroma_format_idc in (1, 2):
            NumC8x8 = 4 // (bs.sps.SubWidthC * bs.sps.SubHeightC)
            for iCbCr in range(2):
                if (self.CodedBlockPatternChroma & 3) and startIdx == 0:
                    ChromaDCLevel[iCbCr] = self.residual_block(
                                            ChromaDCLevel.get(iCbCr), 
                                            0, 
                                            4 * NumC8x8 - 1, 
                                            4 * NumC8x8, 
                                            "ChromaDCLevel", 
                                            bs, 
                                            slice,
                                        )
                else:
                    ChromaDCLevel[iCbCr] = {}
                    # for i in range(4 * NumC8x8):
                    #     ChromaDCLevel[iCbCr][i] = 0

            for iCbCr in range(2):
                ChromaACLevel[iCbCr] = {}
                self.iCbCr = iCbCr
                self.chroma4x4BlkIdxTotalCoeff[iCbCr] = {}
                for i8x8 in range(NumC8x8):
                    for i4x4 in range(4):
                        if self.CodedBlockPatternChroma & 2:
                            self.chroma4x4BlkIdx = i8x8 * 4 + i4x4
                            ChromaACLevel[iCbCr][i8x8 * 4+ i4x4] = self.residual_block(
                                                                        ChromaACLevel[iCbCr].get(i8x8 * 4+ i4x4), 
                                                                        max(0, startIdx - 1), 
                                                                        endIdx - 1, 
                                                                        15, 
                                                                        "ChromaACLevel", 
                                                                        bs, 
                                                                        slice,
                                                                    )
                        else:
                            ChromaACLevel[iCbCr][i8x8 * 4 + i4x4] = {}
                            # for i in range(15):
                            #     ChromaACLevel[iCbCr][i8x8 * 4 + i4x4][i] = 0

        elif bs.sps.ChromaArrayType == 3:
            raise ("未支持")
        self.Intra16x16DCLevel = Intra16x16DCLevel
        self.Intra16x16ACLevel = Intra16x16ACLevel
        self.LumaLevel4x4 = LumaLevel4x4
        self.LumaLevel8x8 = LumaLevel8x8
        self.ChromaDCLevel = ChromaDCLevel
        self.ChromaACLevel = ChromaACLevel
        # print( "",
        #     "Intra16x16DCLevel", Intra16x16DCLevel, "\n", 
        #     "Intra16x16ACLevel", Intra16x16ACLevel, "\n",
        #     "LumaLevel4x4", LumaLevel4x4, "\n",
        #     "LumaLevel8x8", LumaLevel8x8, "\n",
        #     "ChromaDCLevel", ChromaDCLevel, "\n",
        #     "ChromaACLevel", ChromaACLevel, "\n",
        # )

    def residual_luma(self, i16x16DClevel, i16x16AClevel, level4x4, level8x8, startIdx, endIdx, bs:BitStream, slice:SliceData):
        if startIdx == 0 and self.mb_type.MbPartPredMode == "Intra_16x16":
            i16x16DClevel = self.residual_block(i16x16DClevel, 0, 15, 16, "Intra16x16DCLevel", bs, slice)
        for i8x8 in range(4):
            if not self.transform_size_8x8_flag or not bs.pps.entropy_coding_mode_flag:
                for i4x4 in range(4):
                    if self.CodedBlockPatternLuma & (1 << i8x8):
                        if self.mb_type.MbPartPredMode == "Intra_16x16":
                            i16x16AClevel[i8x8 * 4 + i4x4] = self.residual_block(i16x16AClevel.get(i8x8 * 4 + i4x4), max(0, startIdx - 1), endIdx - 1, 15, "Intra16x16ACLevel", bs, slice)
                        else:
                            self.luma4x4BlkIdx = i8x8 * 4 + i4x4               
                            level4x4[i8x8 * 4 + i4x4] = self.residual_block(level4x4.get(i8x8 * 4 + i4x4), startIdx, endIdx, 16, "LumaLevel4x4", bs, slice)

                    elif self.mb_type.MbPartPredMode == "Intra_16x16":
                        level4x4[i8x8 * 4 + i4x4] = {}
                        # for i in range(15): 
                        #     level4x4[i8x8 * 4 + i4x4][i] = 0
                    else:
                        level4x4[i8x8 * 4 + i4x4] = {}
                        # for i in range(16):
                        #     level4x4[i8x8 * 4 + i4x4][i] = 0
                    if not bs.pps.entropy_coding_mode_flag and self.transform_size_8x8_flag:
                        for i in range(16):
                            level8x8[i8x8][4 * i + i4x4] = level4x4[i8x8 * 4 + i4x4][i]
            elif self.CodedBlockPatternLuma & (1 << i8x8):
                level8x8[i8x8] = self.residual_block(level8x8.get(i8x8), 4 * startIdx, 4 * endIdx + 3, 64, bs, slice)
            else:
                for i in range(64):
                    level8x8[i8x8][i] = 0
        return i16x16DClevel, i16x16AClevel, level4x4, level8x8


    def Parse(self):
        self.Intra4x4PredMode = {}
        self.Intra8x8PredMode = {}

        self.QPY = (self.slice.QPY_prev + self.mb_qp_delta + 52 + 2 * self.bs.sps.QpBdOffsetY ) % (52 + self.bs.sps.QpBdOffsetY) - self.bs.sps.QpBdOffsetY
        self.slice.QPY_prev = self.QPY
        self.QP1Y = self.QPY + self.bs.sps.QpBdOffsetY


        if self.bs.sps.qpprime_y_zero_transform_bypass_flag and self.QP1Y == 0:
            self.TransformBypassModeFlag = True
        else:
            self.TransformBypassModeFlag = False

        if self.mb_type.MbPartPredMode == "Intra_4x4":
            self.scaling(0) # 0 为亮度
            for luma4x4BlkIdx in range(16):
                # z形编码
                self.LumaLevel4x4Zigzag = MbPredMode.Block4x4ZigzagScan(self.LumaLevel4x4[luma4x4BlkIdx])
                # 反量化
                self.LumaLevel4x4Scaling = self.scalingTransformProcess(self.LumaLevel4x4Zigzag, True)
                # 预测
                self.lumaPredSamples = self.Intra4x4Prediction(luma4x4BlkIdx, True)
                luma4x4Data = {}
                for i in range(4):
                    for j in range(4):
                        depthY = (1 << self.bs.sps.BitDepthY) - 1
                        pred = self.lumaPredSamples[luma4x4BlkIdx].get(f"{j}_{i}",0) + self.LumaLevel4x4Scaling[i][j]
                        luma4x4Data[i*4+j] = Clip3(0, depthY, pred)
                # if self.CurrMbAddr == 9:
                #     print(luma4x4BlkIdx, "luma4x4Data->", luma4x4Data)
                    # print(luma4x4BlkIdx, "self.lumaPredSamples->", self.lumaPredSamples[luma4x4BlkIdx])
                    # print(luma4x4BlkIdx, "self.LumaLevel4x4Scaling->", self.LumaLevel4x4Scaling)

                self.lumaDataMerge(luma4x4Data, luma4x4BlkIdx, "4*4")
            self.ChromaResidualProcess(ChromaType.Blue)
            self.ChromaResidualProcess(ChromaType.Red)
        elif self.mb_type.MbPartPredMode == "Intra_16x16":
            self.scaling(0) # 0 为亮度
            c = MbPredMode.Block4x4ZigzagScan(self.Intra16x16DCLevel)
            # 开始反量化
            dcY = self.scalingTransformProcess16x16(c, True)
            dcYToLuma = [
                dcY[0][0], dcY[0][1], dcY[1][0], dcY[1][1],
                dcY[0][2], dcY[0][3], dcY[1][2], dcY[1][3],
                dcY[2][0], dcY[2][1], dcY[3][0], dcY[3][1],
                dcY[2][2], dcY[2][3], dcY[3][2], dcY[3][3]
            ] 
                    #    Intra16x16DCLevel

            rMb = [[0 for _ in range(16)] for _ in range(16)]
            for _4x4BlkIdx in range(16):
                lumaList = {}
                lumaList[0] = dcYToLuma[_4x4BlkIdx]
                for k in range(1, 16):
                    lumaList[k] = self.Intra16x16ACLevel.get(_4x4BlkIdx,{}).get(k - 1, 0)
                c = MbPredMode.Block4x4ZigzagScan(lumaList)
                r = self.scalingTransformProcess(c, True)
                xO = InverseRasterScan(_4x4BlkIdx // 4, 8, 8, 16, 0) + InverseRasterScan(_4x4BlkIdx % 4, 4, 4, 8, 0)
                yO = InverseRasterScan(_4x4BlkIdx // 4, 8, 8, 16, 1) + InverseRasterScan(_4x4BlkIdx % 4, 4, 4, 8, 1)
                for i in range(4):
                    for j in range(4):
                        rMb[xO + j][yO + i] = r[i][j]
            # self.luma16x16PredSamples = 
            # if self.CurrMbAddr == 77:
            self.Intra16x16Prediction()
            
            luma16x16Data = {}
            for i in range(16):
                for j in range(16):
                    luma16x16Data[i*16+j] = Clip3(0, (1 << self.bs.sps.BitDepthY) - 1, self.luma16x16PredSamples.get(f"{j}_{i}",0) + rMb[j][i])

            self.lumaDataMerge(luma16x16Data, 0, "16*16")
            self.ChromaResidualProcess(ChromaType.Blue)
            self.ChromaResidualProcess(ChromaType.Red)
        else :
            print("=============>",self.mb_type.MbPartPredMode)
    
    def scaling(self, iYCbCr:int):

        mbIsInterFlag = False
        if self.mb_type.MbPartPredMode in ("Pred_L0","Pred_L1","BiPred_L0_L1"):
            mbIsInterFlag = True

        weightScale4x4 = MbPredMode.Block4x4ZigzagScan(self.slice.header.ScalingList4x4[iYCbCr + (3 if mbIsInterFlag else 0)])

        v4x4 = [
            [10, 16, 13],
            [11, 18, 14],
            [13, 20, 16],
            [14, 23, 18],
            [16, 25, 20],
            [18, 29, 23],
        ]

        self.LevelScale4x4 = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(6)]
        # normAdjust4x4
        for m in range(6):
            for i in range(4):
                for j in range(4):
                    if i % 2 == 0 and j % 2 == 0:
                        self.LevelScale4x4[m][i][j] = weightScale4x4[i][j] * v4x4[m][0]
                    elif i % 2 == 1 and j % 2 == 1:
                        self.LevelScale4x4[m][i][j] = weightScale4x4[i][j] * v4x4[m][1]
                    else:
                        self.LevelScale4x4[m][i][j] = weightScale4x4[i][j] * v4x4[m][2]

    def scalingTransformProcess(self, c, isLuam) -> dict[int, int]:
        '''
            isLuam: 是否是luma亮度相关，亮度相关是不同的处理方式
        '''
        sMbFlag = 0
        if self.mb_type.MbPartPredMode == "SI" or (self.mb_type.MbPartPredMode == "SP"):
            sMbFlag = 1
        
        qP = 0
        if isLuam and sMbFlag:
            qP = self.slice.header.QSY
        elif isLuam and not sMbFlag:
            qP = self.QP1Y
        elif not isLuam and not sMbFlag:
            qP = self.QP1C
        else:
            qP = self.QSC

        if self.TransformBypassModeFlag:
            raise("未实现")
        


        # 量化过程  
        d = [[0 for _ in range(4)] for _ in range(4)]
        for i in range(4):
            for j in range(4):
                if i == 0 and j == 0 and \
                    (self.mb_type.MbPartPredMode == "Intra_16x16" or not isLuam ):
                    d[0][0] = c[0][0]
                else:
                    if qP >= 24:
                        d[i][j] = (c[i][j] * self.LevelScale4x4[qP % 6][i][j]) << (qP // 6 - 4)
                    else: # //if (qP < 24)
                        d[i][j] = (c[i][j] * self.LevelScale4x4[qP % 6][i][j] + int(pow(2, 3 - qP // 6))) >> (4 - qP // 6)

        # 初始化矩阵
        f = [[0 for _ in range(4)] for _ in range(4)]
        h = [[0 for _ in range(4)] for _ in range(4)]
        r = [[0 for _ in range(4)] for _ in range(4)]

        # 1维反变换：处理每行（水平的）变换
        for i in range(4):
            ei0 = d[i][0] + d[i][2]
            ei1 = d[i][0] - d[i][2]
            ei2 = (d[i][1] >> 1) - d[i][3]
            ei3 = d[i][1] + (d[i][3] >> 1)

            f[i][0] = ei0 + ei3
            f[i][1] = ei1 + ei2
            f[i][2] = ei1 - ei2
            f[i][3] = ei0 - ei3

        # 1维反变换：处理每列（纵向）变换
        for j in range(4):
            g0j = f[0][j] + f[2][j]
            g1j = f[0][j] - f[2][j]
            g2j = (f[1][j] >> 1) - f[3][j]
            g3j = f[1][j] + (f[3][j] >> 1)

            h[0][j] = g0j + g3j
            h[1][j] = g1j + g2j
            h[2][j] = g1j - g2j
            h[3][j] = g0j - g3j

        # 最终结果计算
        for i in range(4):
            for j in range(4):
                r[i][j] = (h[i][j] + 32) >> 6

        return r

    def scalingTransformProcess16x16(self, c, isLuam) -> dict[int, int]:
            qP = 0
            if isLuam:
                qP = self.QP1Y
            else:
                qP = self.QP1C
                
            a = [
                [1,1,1,1],
                [1,1,-1,-1],
                [1,-1,-1,1],
                [1,-1,1,-1],
            ]
            g = [[0 for _ in range(4)] for _ in range(4)]
            f = [[0 for _ in range(4)] for _ in range(4)]
            dcY = [[0 for _ in range(4)] for _ in range(4)]
            
            # 计算 g = a * c
            for i in range(4):
                for j in range(4):
                    for k in range(4):
                        g[i][j] += a[i][k] * c[k][j]

            # 计算 f = g * a
            for i in range(4):
                for j in range(4):
                    for k in range(4):
                        f[i][j] += g[i][k] * a[k][j]

            # 根据 qP 的值计算 dcY
            if qP >= 36:
                for i in range(4):
                    for j in range(4):
                        dcY[i][j] = (f[i][j] * self.LevelScale4x4[qP % 6][0][0]) << (qP // 6 - 6)
            else:
                for i in range(4):
                    for j in range(4):
                        dcY[i][j] = (f[i][j] * self.LevelScale4x4[qP % 6][0][0] + (1 << (5 - qP // 6))) >> (6 - qP // 6)
            return dcY

    def Intra4x4Prediction(self, luma4x4BlkIdx:int, isLuam:bool):
        '''
            4x4块预测
        '''

        xO = InverseRasterScan(luma4x4BlkIdx // 4, 8, 8, 16, 0) + InverseRasterScan(luma4x4BlkIdx % 4, 4, 4, 8, 0)
        yO = InverseRasterScan(luma4x4BlkIdx // 4, 8, 8, 16, 1) + InverseRasterScan(luma4x4BlkIdx % 4, 4, 4, 8, 1)

        referenceCoordinateX = [ -1, -1, -1, -1, -1,  0,  1,  2,  3,  4,  5,  6,  7 ]
        referenceCoordinateY = [ -1,  0,  1,  2,  3, -1, -1, -1, -1, -1, -1, -1, -1 ]
        lumaPredSamples = {}
        # 初始化 samples 数组
        samples = [-1] * 45

        # 定义 P(x, y) 函数
        def P(x, y):
            return samples[(y + 1) * 9 + (x + 1)]

        def set_P(x, y, value):
            index = (y + 1) * 9 + (x + 1)  # 计算索引
            samples[index] = value  

        for i in range(13):
            maxW = 0
            maxH = 0
            if isLuam :
                maxW = maxH = 16
            else:
                maxH = self.bs.sps.MbHeightC
                maxW = self.bs.sps.MbWidthC
            x = referenceCoordinateX[i]
            y = referenceCoordinateY[i]
            xN = xO + x
            yN = yO + y
            mbAddrN, xW, yW = self.slice.getMbAddrNAndLuma4x4BlkIdxN(xN, yN, maxW, maxH)
            if mbAddrN == None \
                or (self.slice.header.slice_type == SliceType.SI and self.bs.pps.constrained_intra_pred_flag) \
                or (x > 3 and (luma4x4BlkIdx == 3 or luma4x4BlkIdx == 11)):
                # set_P(x, y, -1)
                pass
            else:
                xM = InverseRasterScan(mbAddrN.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInMbs * 16, 0)
                yM = InverseRasterScan(mbAddrN.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInMbs * 16, 1)
                set_P(x, y, self.slice.lumaData.get(xM + xW, {}).get(yM + yW,0))
                # print(x,y, xM + xW, yM + yW, P(x, y), self.slice.lumaData.get(xM + xW, {}).get(yM + yW,0))
                # print(self.slice.lumaData)
                # exit(0)
                # if self.slice.CurrMbAddr == 9:
                #     print(luma4x4BlkIdx, x, y, xM + xW, yM + yW, self.slice.lumaData.get(xM + xW, {}).get(yM + yW,0))

        # print("luma4x4BlkIdx", luma4x4BlkIdx, samples)


        if P(4, -1) < 0 and P(5, -1) < 0 and P(6, -1) < 0 and P(7, -1) < 0 and P(3, -1) >= 0:
            set_P(4, -1, P(3, -1))
            set_P(5, -1, P(3, -1))
            set_P(6, -1, P(3, -1))
            set_P(7, -1, P(3, -1))
        
        self.Intra4x4PredictionMode(luma4x4BlkIdx, isLuam)

        intra4x4PredMode = self.Intra4x4PredMode[luma4x4BlkIdx]

        # if self.slice.CurrMbAddr == 9:
            # print("samples", samples)
            # print("intra4x4PredMode", luma4x4BlkIdx, intra4x4PredMode)


        # 9种预测模型
        lumaPredSamples[luma4x4BlkIdx] = {}

        if intra4x4PredMode == Intra4x4PredMode.Intra_4x4_Vertical:  # 垂直
            if all(P(x, -1) >= 0 for x in range(4)):
                for y in range(4):
                    for x in range(4):
                        lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = P(x, -1)
        elif intra4x4PredMode == Intra4x4PredMode.Intra_4x4_Horizontal:  # 水平
            if all(P(-1, y) >= 0 for y in range(4)):
                for y in range(4):
                    for x in range(4):
                        lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = P(-1, y)
        elif intra4x4PredMode == Intra4x4PredMode.Intra_4x4_DC:  # 均值
            val = 0
            if all(P(x, -1) >= 0 for x in range(4)) and all(P(-1, y) >= 0 for y in range(4)):
                val = (sum(P(x, -1) for x in range(4)) + sum(P(-1, y) for y in range(4)) + 4) >> 3
            elif any(P(x, -1) < 0 for x in range(4)) and all(P(-1, y) >= 0 for y in range(4)):
                val = (sum(P(-1, y) for y in range(4)) + 2) >> 2
            elif any(P(-1, y) < 0 for y in range(4)) and all(P(x, -1) >= 0 for x in range(4)):
                val = (sum(P(x, -1) for x in range(4)) + 2) >> 2
            else:
                val = 1 << (self.bs.sps.BitDepthY - 1)

            for x in range(4):
                for y in range(4):
                    lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = val
        elif intra4x4PredMode == Intra4x4PredMode.Intra_4x4_Diagonal_Down_Left:
            if all(P(x, -1) >= 0 for x in range(8)):
                for y in range(4):
                    for x in range(4):
                        if x == 3 and y == 3:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (P(6, -1) + 3 * P(7, -1) + 2) >> 2
                        else:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (P(x + y, -1) + 2 * P(x + y + 1, -1) + P(x + y + 2, -1) + 2) >> 2
        elif intra4x4PredMode == Intra4x4PredMode.Intra_4x4_Diagonal_Down_Right:
            if all(P(x, -1) >= 0 for x in range(4)) and all(P(-1, y) >= 0 for y in range(4)):
                for y in range(4):
                    for x in range(4):
                        if x > y:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (P(x - y - 2, -1) + 2 * P(x - y - 1, -1) + P(x - y, -1) + 2) >> 2
                        elif x < y:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (P(-1, y - x - 2) + 2 * P(-1, y - x - 1) + P(-1, y - x) + 2) >> 2
                        else:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (P(0, -1) + 2 * P(-1, -1) + P(-1, 0) + 2) >> 2
        elif intra4x4PredMode == Intra4x4PredMode.Intra_4x4_Vertical_Right:
            if all(P(x, -1) >= 0 for x in range(4)) and all(P(-1, y) >= 0 for y in range(4)):
                for y in range(4):
                    for x in range(4):
                        zVR = 2 * x - y

                        if zVR in {0, 2, 4, 6}:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (P(x - (y >> 1) - 1, -1) + P(x - (y >> 1), -1) + 1) >> 1
                        elif zVR in {1, 3, 5}:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (P(x - (y >> 1) - 2, -1) + 2 * P(x - (y >> 1) - 1, -1) + P(x - (y >> 1), -1) + 2) >> 2
                        elif zVR == -1:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (P(-1, 0) + 2 * P(-1, -1) + P(0, -1) + 2) >> 2
                        else:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (P(-1, y - 1) + 2 * P(-1, y - 2) + P(-1, y - 3) + 2) >> 2
        elif intra4x4PredMode == Intra4x4PredMode.Intra_4x4_Horizontal_Down:
                if all(P(x, -1) >= 0 for x in range(4)) and all(P(-1, y) >= 0 for y in range(4)) and P(-1, -1) >= 0:
                    for y in range(4):
                        for x in range(4):
                            zHD = 2 * y - x
                            if zHD in [0, 2, 4, 6]:
                                lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (
                                    P(-1, y - (x >> 1) - 1) + P(-1, y - (x >> 1)) + 1) >> 1
                            elif zHD in [1, 3, 5]:
                                lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (
                                    P(-1, y - (x >> 1) - 2) + 2 * P(-1, y - (x >> 1) - 1) + P(-1, y - (x >> 1)) + 2) >> 2
                            elif zHD == -1:
                                lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (
                                    P(-1, 0) + 2 * P(-1, -1) + P(0, -1) + 2) >> 2
                            else:
                                lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (
                                    P(x - 1, -1) + 2 * P(x - 2, -1) + P(x - 3, -1) + 2) >> 2
        elif intra4x4PredMode == Intra4x4PredMode.Intra_4x4_Vertical_Left:
            if all(P(x, -1) >= 0 for x in range(8)):
                for y in range(4):
                    for x in range(4):
                        if y in [0, 2]:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (
                                P(x + (y >> 1), -1) + P(x + (y >> 1) + 1, -1) + 1) >> 1
                        else:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (
                                P(x + (y >> 1), -1) + 2 * P(x + (y >> 1) + 1, -1) + P(x + (y >> 1) + 2, -1) + 2) >> 2
        elif intra4x4PredMode == Intra4x4PredMode.Intra_4x4_Horizontal_Up:
            if all(P(-1, y) >= 0 for y in range(4)):
                for y in range(4):
                    for x in range(4):
                        zHU = x + 2 * y
                        if zHU in [0, 2, 4]:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (
                                P(-1, y + (x >> 1)) + P(-1, y + (x >> 1) + 1) + 1) >> 1
                        elif zHU in [1, 3]:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (
                                P(-1, y + (x >> 1)) + 2 * P(-1, y + (x >> 1) + 1) + P(-1, y + (x >> 1) + 2) + 2) >> 2
                        elif zHU == 5:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = (
                                P(-1, 2) + 3 * P(-1, 3) + 2) >> 2
                        else:
                            lumaPredSamples[luma4x4BlkIdx][f"{x}_{y}"] = P(-1, 3)

        return lumaPredSamples

            
        # 4x4块预测

    def Intra4x4PredictionMode(self, luma4x4BlkIdx, isLuam:bool):
        '''
            4x4块预测模式
        '''
        x = InverseRasterScan(luma4x4BlkIdx // 4, 8, 8, 16, 0) + InverseRasterScan(luma4x4BlkIdx % 4, 4, 4, 8, 0)
        y = InverseRasterScan(luma4x4BlkIdx // 4, 8, 8, 16, 1) + InverseRasterScan(luma4x4BlkIdx % 4, 4, 4, 8, 1)
        maxW = maxH = 16
        if not isLuam :
            maxH = self.bs.sps.MbHeightC
            maxW = self.bs.sps.MbWidthC
        mbAddrA, xW, yW = self.slice.getMbAddrNAndLuma4x4BlkIdxN(x-1, y, maxW, maxH)
        if mbAddrA != None:
            luma4x4BlkIdxA = 8 * (yW // 8) + 4 * (xW // 8) + 2 * ((yW % 8) // 4) + ((xW % 8) // 4)
        mbAddrB, xW, yW = self.slice.getMbAddrNAndLuma4x4BlkIdxN(x + 0, y + (-1), maxW, maxH)
        if mbAddrB != None:
            luma4x4BlkIdxB = 8 * (yW // 8) + 4 * (xW // 8) + 2 * ((yW % 8) // 4) + ((xW % 8) // 4)

        intraMxMPredModeA = None
        intraMxMPredModeB = None

        dcPredModePredictedFlag = 0
        if  mbAddrA == None or mbAddrB == None or \
            (mbAddrA != None and mbAddrA.mb_type.isInterProd() and self.bs.pps.constrained_intra_pred_flag) or \
            (mbAddrB != None and mbAddrB.mb_type.isInterProd() and self.bs.pps.constrained_intra_pred_flag):
            dcPredModePredictedFlag = 1

        if dcPredModePredictedFlag or \
            (mbAddrA != None and mbAddrA.mb_type.MbPartPredMode not in ("Intra_4x4", "Intra_8x8")): 
            intraMxMPredModeA = 2
        else:
            # 根据左侧宏块的模式选择对应的预测模式
            if mbAddrA.mb_type.MbPartPredMode == "Intra_4x4":
                intraMxMPredModeA = mbAddrA.Intra4x4PredMode[luma4x4BlkIdxA]
            else:  # Intra_8x8
                intraMxMPredModeA = mbAddrA.Intra8x8PredMode[luma4x4BlkIdxA >> 2]

        # 处理上方相邻宏块的预测模式
        if dcPredModePredictedFlag or \
            (mbAddrB != None and mbAddrB.mb_type.MbPartPredMode not in ("Intra_4x4", "Intra_8x8")):
            intraMxMPredModeB = 2
        else:
            # 根据上方宏块的模式选择对应的预测模式
            if mbAddrB.mb_type.MbPartPredMode == "Intra_4x4":
                intraMxMPredModeB = mbAddrB.Intra4x4PredMode[luma4x4BlkIdxB]
            else:  # Intra_8x8
                intraMxMPredModeB = mbAddrB.Intra8x8PredMode[luma4x4BlkIdxB >> 2]

        # 从左侧和上方相邻块的预测模式中选取较小的一个作为预先定义模式
        predIntra4x4PredMode = min(intraMxMPredModeA, intraMxMPredModeB)

        # 判断当前块的预测模式
        if self.prev_intra4x4_pred_mode_flag[luma4x4BlkIdx]:
            # 如果标志位为 1，则使用预定义模式
            self.Intra4x4PredMode[luma4x4BlkIdx] = predIntra4x4PredMode
        else:
            # 根据 rem_intra4x4_pred_mode 决定预测模式
            # print("predIntra4x4PredMode", predIntra4x4PredMode,intraMxMPredModeA, intraMxMPredModeB )
            if self.rem_intra4x4_pred_mode[luma4x4BlkIdx] < predIntra4x4PredMode:
                self.Intra4x4PredMode[luma4x4BlkIdx] = self.rem_intra4x4_pred_mode[luma4x4BlkIdx]
            else:
                self.Intra4x4PredMode[luma4x4BlkIdx] = self.rem_intra4x4_pred_mode[luma4x4BlkIdx] + 1

    def Intra16x16Prediction(self, isLuam:bool = True):
        # Relative coordinates to the top-left corner

        reference_coordinate_x = [ -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15 ]
        reference_coordinate_y = [ -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1 ]

        p = [-1] * (17 * 17)
        def P(x, y):
            return p[(y + 1) * 17 + (x + 1)]

        def set_p(x, y, value):
            p[(y + 1) * 17 + (x + 1)] = value
        
        for i in range(33):
            max_w = 16 if isLuam else self.bs.sps.MbWidthC
            max_h = 16 if isLuam else self.bs.sps.MbHeightC

            x = reference_coordinate_x[i]
            y = reference_coordinate_y[i]
           
            mbAddrN, xW, yW = self.slice.getMbAddrNAndLuma4x4BlkIdxN(x, y, max_w, max_h, )

            if (mbAddrN == None or
                (mbAddrN.mb_type.isInterProd() and self.bs.pps.constrained_intra_pred_flag) or
                (mbAddrN.slice.header.slice_type == SliceType.SI and self.bs.pps.constrained_intra_pred_flag)):
                set_p(x, y, -1)
            else:
                xM = InverseRasterScan(mbAddrN.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInSamplesL, 0)
                yM = InverseRasterScan(mbAddrN.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInSamplesL, 1)
                set_p(x, y, self.slice.lumaData[xM + xW][yM + yW])
                # if self.CurrMbAddr == 77:
                #     print(x, y, xM + xW, yM + yW, int(self.slice.lumaData[xM + xW][yM + yW]))

        Intra16x16PredMode = self.mb_type.Intra16x16PredMode

        self.luma16x16PredSamples = {}

        if Intra16x16PredMode == 0:  # 垂直
            if all(P(x, -1) >= 0 for x in range(16)):
                for y in range(16):
                    for x in range(16):
                        self.luma16x16PredSamples[f"{x}_{y}"] = P(x, -1)
        elif Intra16x16PredMode == 1:  # 水平
            if all(P(-1, y) >= 0 for y in range(16)):
                for y in range(16):
                    for x in range(16):
                        self.luma16x16PredSamples[f"{x}_{y}"] = P(-1, y)
        elif Intra16x16PredMode == 2:  # 四舍五入求均值
            val = 0

            if all(P(x, -1) >= 0 for x in range(16)) and all(P(-1, y) >= 0 for y in range(16)):
                val = (sum(P(x, -1) for x in range(16)) + sum(P(-1, y) for y in range(16)) + 16) >> 5

            elif not all(P(x, -1) >= 0 for x in range(16)) and all(P(-1, y) >= 0 for y in range(16)):
                val = (sum(P(-1, y) for y in range(16)) + 8) >> 4

            elif all(P(x, -1) >= 0 for x in range(16)) and not all(P(-1, y) >= 0 for y in range(16)):
                val = (sum(P(x, -1) for x in range(16)) + 8) >> 4

            else:
                val = 1 << (self.bs.sps.BitDepthY - 1)

            for x in range(16):
                for y in range(16):
                    self.luma16x16PredSamples[f"{x}_{y}"] = val
        elif Intra16x16PredMode == 3:  # 平面预测
            if all(P(x, -1) >= 0 for x in range(16)) and all(P(-1, y) >= 0 for y in range(16)):
                H = sum((x + 1) * (P(8 + x, -1) - P(6 - x, -1)) for x in range(8))
                V = sum((y + 1) * (P(-1, 8 + y) - P(-1, 6 - y)) for y in range(8))

                a = 16 * (P(-1, 15) + P(15, -1))
                b = (5 * H + 32) >> 6
                c = (5 * V + 32) >> 6

                for y in range(16):
                    for x in range(16):
                        self.luma16x16PredSamples[f"{x}_{y}"] = Clip3(
                            0, (1 << self.bs.sps.BitDepthY) - 1, (a + b * (x - 7) + c * (y - 7) + 16) >> 5
                        )

    def ChromaPrediction(self, chroma):
        MbWidthC = self.bs.sps.MbWidthC
        MbHeightC = self.bs.sps.MbHeightC

        maxSamplesVal = MbWidthC + MbHeightC + 1
        referenceCoordinateX = {}
        referenceCoordinateY = {}

        # 第一个 for 循环
        for i in range(-1, MbHeightC):
            referenceCoordinateX[i + 1] = -1
            referenceCoordinateY[i + 1] = i

        # 第二个 for 循环
        for i in range(MbWidthC):
            referenceCoordinateX[MbHeightC + 1 + i] = i
            referenceCoordinateY[MbHeightC + 1 + i] = -1
        
        # 初始化 samples 数组
        samples = [-1] * (MbWidthC + 1) * (MbHeightC + 1)
        # 定义 P(x, y) 函数
        def P(x, y):
            return samples[(y + 1) * 9 + (x + 1)]
        def set_P(x, y, value):
            index = (y + 1) * 9 + (x + 1)  # 计算索引
            samples[index] = value  

        for i in range(maxSamplesVal):
            x = referenceCoordinateX[i]
            y = referenceCoordinateY[i]

            mbAddrN, xW, yW = self.slice.getMbAddrNAndLuma4x4BlkIdxN(x, y, MbWidthC, MbHeightC)

            if mbAddrN == None or \
			(mbAddrN.mb_type.isInterProd and self.bs.pps.constrained_intra_pred_flag) or \
			(mbAddrN.slice.header.slice_type == SliceType.SI and self.bs.pps.constrained_intra_pred_flag and self.slice.header.slice_type != SliceType.SI):
                pass
            else:
                xL = InverseRasterScan(mbAddrN.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInSamplesL, 0)
                yL = InverseRasterScan(mbAddrN.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInSamplesL, 1)
                xM = (xL >> 4) * MbWidthC
                yM = ((yL >> 4) * MbHeightC) + (yL % 2)
                if chroma == ChromaType.Blue:
                    set_P(x, y, self.slice.chromaCbData.get(xM + xW,{}).get(yM + yW,0))
                else:
                    set_P(x, y, self.slice.chromaCrData.get(xM + xW,{}).get(yM + yW,0))

        self.chromaPredSamples = [[0 for _ in range(16)] for _ in range(8)]

        # print(self.intra_chroma_pred_mode)

        if self.intra_chroma_pred_mode == 0:
            for chroma4x4BlkIdx in range(1 << (self.bs.sps.ChromaArrayType + 1)):
                xO = InverseRasterScan(chroma4x4BlkIdx, 4, 4, 8, 0)
                yO = InverseRasterScan(chroma4x4BlkIdx, 4, 4, 8, 1)

                val = 0
                if (xO == 0 and yO == 0) or (xO > 0 and yO > 0):
                    if (P(0 + xO, -1) >= 0 and P(1 + xO, -1) >= 0 and P(2 + xO, -1) >= 0 and P(3 + xO, -1) >= 0 and
                        P(-1, 0 + yO) >= 0 and P(-1, 1 + yO) >= 0 and P(-1, 2 + yO) >= 0 and P(-1, 3 + yO) >= 0):
                        val = (P(0 + xO, -1) + P(1 + xO, -1) + P(2 + xO, -1) + P(3 + xO, -1) +
                            P(-1, 0 + yO) + P(-1, 1 + yO) + P(-1, 2 + yO) + P(-1, 3 + yO) + 4) >> 3
                    elif not (P(0 + xO, -1) >= 0 and P(1 + xO, -1) >= 0 and P(2 + xO, -1) >= 0 and P(3 + xO, -1) >= 0) and \
                        (P(-1, 0 + yO) >= 0 and P(-1, 1 + yO) >= 0 and P(-1, 2 + yO) >= 0 and P(-1, 3 + yO) >= 0):
                        val = (P(-1, 0 + yO) + P(-1, 1 + yO) + P(-1, 2 + yO) + P(-1, 3 + yO) + 2) >> 2
                    elif (P(0 + xO, -1) > 0 and P(1 + xO, -1) > 0 and P(2 + xO, -1) > 0 and P(3 + xO, -1) > 0) and \
                        not (P(-1, 0 + yO) > 0 and P(-1, 1 + yO) > 0 and P(-1, 2 + yO) > 0 and P(-1, 3 + yO) > 0):
                        val = (P(0 + xO, -1) + P(1 + xO, -1) + P(2 + xO, -1) + P(3 + xO, -1) + 2) >> 2
                    else:
                        val = (1 << (self.bs.sps.BitDepthC - 1))
                elif xO > 0 and yO == 0:
                    if P(0 + xO, -1) >= 0 and P(1 + xO, -1) >= 0 and P(2 + xO, -1) >= 0 and P(3 + xO, -1) >= 0:
                        val = (P(0 + xO, -1) + P(1 + xO, -1) + P(2 + xO, -1) + P(3 + xO, -1) + 2) >> 2
                    elif P(-1, 0 + yO) >= 0 and P(-1, 1 + yO) >= 0 and P(-1, 2 + yO) >= 0 and P(-1, 3 + yO) > 0:
                        val = (P(-1, 0 + yO) + P(-1, 1 + yO) + P(-1, 2 + yO) + P(-1, 3 + yO) + 2) >> 2
                    else:
                        val = (1 << (self.bs.sps.BitDepthC - 1))
                elif xO == 0 and yO > 0:
                    if P(-1, 0 + yO) >= 0 and P(-1, 1 + yO) >= 0 and P(-1, 2 + yO) >= 0 and P(-1, 3 + yO) > 0:
                        val = (P(-1, 0 + yO) + P(-1, 1 + yO) + P(-1, 2 + yO) + P(-1, 3 + yO) + 2) >> 2
                    elif P(0 + xO, -1) >= 0 and P(1 + xO, -1) >= 0 and P(2 + xO, -1) >= 0 and P(3 + xO, -1) > 0:
                        val = (P(0 + xO, -1) + P(1 + xO, -1) + P(2 + xO, -1) + P(3 + xO, -1) + 2) >> 2
                    else:
                        val = (1 << (self.bs.sps.BitDepthC - 1))
                for y in range(4):
                    for x in range(4):
                        self.chromaPredSamples[x + xO][y + yO] = val
        elif self.intra_chroma_pred_mode == 1:
            flag = 1
            for y in range(MbHeightC):
                if P(-1, y) < 0:
                    flag = 0
                    break
            if flag:
                for y in range(MbHeightC):
                    for x in range(MbWidthC):
                        self.chromaPredSamples[x][y] = P(-1, y)
        elif self.intra_chroma_pred_mode == 2:
            flag = 1
            for y in range(MbHeightC):
                if P(x, -1) < 0:
                    flag = 0
                    break
            if flag:
                for y in range(MbHeightC):
                    for x in range(MbWidthC):
                        self.chromaPredSamples[x][y] = P(x, -1)
        elif self.intra_chroma_pred_mode == 3:
            flag = 1
            for y in range(MbHeightC):
                if P(-1, y) < 0:
                    flag = 0
                    break
            if flag:

                xCF = 4 if self.bs.sps.ChromaArrayType == 3 else 0
                yCF = 4 if self.bs.sps.ChromaArrayType != 1 else 0
                H = 0
                V = 0
                for x1 in range(4 + xCF):
                    H += (x1 + 1) * (P(4 + xCF + x1, -1) - P(2 + xCF - x1, -1))
                for y1 in range(4 + yCF):
                    V += (y1 + 1) * (P(-1, 4 + yCF + y1) - P(-1, 2 + yCF - y1))
                a = 16 * (P(-1, MbHeightC - 1) + P(MbWidthC - 1, -1))
                b = ((34 - 29 * (self.bs.sps.ChromaArrayType == 3)) * H + 32) >> 6
                c = ((34 - 29 * (self.bs.sps.ChromaArrayType != 1)) * V + 32) >> 6

                # 填充 chromaPredSamples
                for y in range(MbHeightC):
                    for x in range(MbWidthC):
                        self.chromaPredSamples[x][y] = Clip3(
                            0, (1 << self.bs.sps.BitDepthC) - 1,
                            (a + b * (x - 3 - xCF) + c * (y - 3 - yCF) + 16) >> 5
                        )

    def ChromaDCProcess(self, c, MbWidthC, MbHeightC, chroma):

        qPOffset = 0
        if chroma == ChromaType.Blue:
            qPOffset = self.bs.pps.chroma_qp_index_offset
        else:
            qPOffset = self.bs.pps.second_chroma_qp_index_offset
            # print("==->", qPOffset)
        qPI = Clip3(-self.bs.sps.QpBdOffsetC, 51, self.QPY + qPOffset)
   
        if qPI < 30:
            self.QPC = qPI
        else:
            QPCs = [ 29, 30, 31, 32, 32, 33, 34, 34, 35, 35, 36, 36, 37, 37, 37, 38, 38, 38, 39, 39, 39, 39 ]
            self.QPC = QPCs[qPI - 30]
        self.QP1C = self.QPC + self.bs.sps.QpBdOffsetC

        # getChromaQuantisationParameters(isChromaCb);
        qP = self.QP1C

        

        dcC = [[0 for _ in range(2)] for _ in range(4)]
        if self.bs.sps.ChromaArrayType == 1:
            a = [
				[1, 1],
				[1,-1]
			]
            g = [[0 for _ in range(2)] for _ in range(2)]
            f= [[0 for _ in range(2)] for _ in range(2)]

            for i in range(2):
                for j in range(2):
                    for k in range(2):
                        g[i][j] += a[i][k] * c[k][j]
            for i in range(2):
                for j in range(2):
                    for k in range(2):
                        f[i][j] += g[i][k] * a[k][j]
            for i in range(2):
                for j in range(2):
                    dcC[i][j] = ((f[i][j] * self.LevelScale4x4[qP % 6][0][0]) << (qP // 6)) >> 5
        
        elif self.bs.sps.ChromaArrayType == 2:
            a = [
				[1,1,1,1],
				[1,1,-1,-1],
				[1,-1,-1,1],
				[1,-1,1,-1],
			]
            b = [[ 1,1],[1,-1]]
            g = [[0 for _ in range(2)] for _ in range(4)]
            f= [[0 for _ in range(2)] for _ in range(4)]
            for i in range(4):
                for j in range(2):
                    for k in range(4):
                        g[i][j] += a[i][k] * c[k][j]
            for i in range(4):
                for j in range(2):
                    for k in range(4):
                        f[i][j] += g[i][k] * b[k][j]
            qPDc = qP + 3
            if qPDc >= 36:
                for i in range(4):
                    for j in range(2):
                        dcC[i][j] = (f[i][j] * self.LevelScale4x4[qPDc % 6][0][0]) << (qPDc // 6 - 6)
            else:
                for i in range(4):
                    for j in range(2):
                        dcC[i][j] = (f[i][j] * self.LevelScale4x4[qPDc % 6][0][0] + int(pow(2, 5 - qPDc // 6))) >> (6 - qP // 6)

        else:
            raise('==')
        
        return dcC

    def ChromaResidualProcess(self, chroma: ChromaType):
        if self.bs.sps.ChromaArrayType in (0,3):
            raise(self.bs.sps.ChromaArrayType)

        if self.bs.sps.ChromaArrayType == 1: #  //420
            c = [[0 for _ in range(2)] for _ in range(2)]
            c[0][0] = self.ChromaDCLevel[chroma].get(0,0)
            c[0][1] = self.ChromaDCLevel[chroma].get(1,0)
            c[1][0] = self.ChromaDCLevel[chroma].get(2,0)
            c[1][1] = self.ChromaDCLevel[chroma].get(3,0)
        elif self.bs.sps.ChromaArrayType == 2: #  //422
            c = [[0 for _ in range(2)] for _ in range(4)]
            c[0][0] = self.ChromaDCLevel[chroma].get(0,0)
            c[0][1] = self.ChromaDCLevel[chroma].get(1,0)
            c[1][0] = self.ChromaDCLevel[chroma].get(2,0)
            c[1][1] = self.ChromaDCLevel[chroma].get(3,0)
            c[2][0] = self.ChromaDCLevel[chroma].get(4,0)
            c[2][1] = self.ChromaDCLevel[chroma].get(5,0)
            c[3][0] = self.ChromaDCLevel[chroma].get(6,0)
            c[3][1] = self.ChromaDCLevel[chroma].get(7,0)
        
        dcC = self.ChromaDCProcess(c, 0, 0, chroma)
        # print("dcC", dcC)

        dcCToChroma = [
            dcC[0][0], dcC[0][1],
            dcC[1][0], dcC[1][1],
            dcC[2][0], dcC[2][1],
            dcC[3][0], dcC[3][1],
        ]

        rMb = [[0 for _ in range(16)] for _ in range(8)]
        numChroma4x4Blks = (self.bs.sps.MbWidthC // 4) * (self.bs.sps.MbHeightC // 4)
        for chroma4x4BlkIdx in range(numChroma4x4Blks):
            chromaList = {}
            chromaList[0] = dcCToChroma[chroma4x4BlkIdx]
            for k in range(1,16):
                chromaList[k] = self.ChromaACLevel[chroma].get(chroma4x4BlkIdx,{}).get(k - 1,0)
            c = MbPredMode.Block4x4ZigzagScan(chromaList)
            r = self.scalingTransformProcess(c, False)
            # print(chromaList)
	        # 对c进行变换
            xO = InverseRasterScan(chroma4x4BlkIdx, 4, 4, 8, 0)
            yO = InverseRasterScan(chroma4x4BlkIdx, 4, 4, 8, 1)
            for i in range(4):
                for j in range(4):
                    rMb[xO + j][yO + i] = r[i][j]
                    # print(i, j, r[i][j])
        
        chromaData = {}
        self.ChromaPrediction(chroma)

        for i in range(self.bs.sps.MbWidthC):
            for j in range(self.bs.sps.MbHeightC):
                chromaData[i * self.bs.sps.MbWidthC + j] = Clip3(0, (1 << self.bs.sps.BitDepthC) - 1, self.chromaPredSamples[j][i] + rMb[j][i])

        # if self.CurrMbAddr < 2:
        #     # if self.CurrMbAddr == 11 and
        #     if chroma == ChromaType.Red:
        #         print("chromaData", chromaData)
        #         # print("rMb", rMb)
        #         # print("self.chromaPredSamples", self.chromaPredSamples)
        # else:
        #     exit(0)

        self.chromaDataMerge(chromaData, chroma)

    def chromaDataMerge(self, luma4x4Data, chroma):
        xP = InverseRasterScan(self.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInMbs * 16, 0)
        yP = InverseRasterScan(self.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInMbs * 16, 1)

        xO = 0
        yO = 0

        MbWidthC = self.bs.sps.MbWidthC
        MbHeightC = self.bs.sps.MbHeightC
        if self.bs.sps.ChromaArrayType == 1 or self.bs.sps.ChromaArrayType == 2:
            yO = 0
            for i in range(MbWidthC):
                for j in range(MbHeightC):
                    if chroma == ChromaType.Blue:
                        if (xP // self.bs.sps.SubWidthC + xO + j) not in self.slice.chromaCbData:
                            self.slice.chromaCbData[xP // self.bs.sps.SubWidthC + xO + j] = {}
                        self.slice.chromaCbData[xP // self.bs.sps.SubWidthC + xO + j][yP // self.bs.sps.SubHeightC + yO + i] = luma4x4Data[i * MbWidthC + j]
                    else:
                        if (xP // self.bs.sps.SubWidthC + xO + j) not in self.slice.chromaCrData:
                            self.slice.chromaCrData[xP // self.bs.sps.SubWidthC + xO + j] = {}
                        self.slice.chromaCrData[xP // self.bs.sps.SubWidthC + xO + j][yP // self.bs.sps.SubHeightC + yO + i] = luma4x4Data[i * MbWidthC + j]

    def lumaDataMerge(self, luma4x4Data, luma4x4BlkIdx, mode):
        xP = InverseRasterScan(self.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInMbs * 16, 0)
        yP = InverseRasterScan(self.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInMbs * 16, 1)

        xO = 0
        yO = 0
        nE = 0
        if mode == "16*16":
            nE = 16
        elif mode == "4*4":
            xO = InverseRasterScan(luma4x4BlkIdx // 4, 8, 8, 16, 0) + InverseRasterScan(luma4x4BlkIdx % 4, 4, 4, 8, 0)
            yO = InverseRasterScan(luma4x4BlkIdx // 4, 8, 8, 16, 1) + InverseRasterScan(luma4x4BlkIdx % 4, 4, 4, 8, 1)
            nE = 4
        else: #//8*8
            xO = InverseRasterScan(luma4x4BlkIdx, 8, 8, 16, 0)
            yO = InverseRasterScan(luma4x4BlkIdx, 8, 8, 16, 1)
            nE = 8
        for i in range(nE):
            for j in range(nE):
                if (xP + xO + j) not in self.slice.lumaData:
                    self.slice.lumaData[xP + xO + j] = {}
                # if self.slice.CurrMbAddr == 9:
                #     print(f"===> {j} {xP} {xO} {i} {yP} {yO} {i * nE + j}")
                # if xP + xO + j == 15 and yP + yO + i == 112:
                #     raise BaseException(self.CurrMbAddr)
                self.slice.lumaData[xP + xO + j][yP + yO + i] = luma4x4Data[i * nE + j]



    # def Intra4x4pred(self, luma4x4BlkIdx, isLuam):
    #     """
    #     4x4亮度块预测过程
    #     """
    #     xO = InverseRasterScan(luma4x4BlkIdx // 4, 8, 8, 16, 0) + InverseRasterScan(luma4x4BlkIdx % 4, 4, 4, 8, 0)
    #     yO = InverseRasterScan(luma4x4BlkIdx // 4, 8, 8, 16, 1) + InverseRasterScan(luma4x4BlkIdx % 4, 4, 4, 8, 1)

    #     # 13个预测样本
    #     samplesPred4x4L = {
    #         "x": (-1, -1, -1, -1, -1,  0,  1,  2,  3,  4,  5,  6,  7),
    #         "y": (-1,  0,  1,  2,  3, -1, -1, -1, -1, -1, -1, -1, -1)
    #     }

    #     P = Matrix(-1)

    #     maxW, maxH = (16, 16) if isLuam else (self.bs.sps.MbWidthC, self.bs.sps.MbHeightC)

    #     for i in range(13):
    #         x = samplesPred4x4L["x"][i]
    #         y = samplesPred4x4L["y"][i]
    #         xN = xO + x
    #         yN = yO + y
    #         mbAddrN, xW, yW = self.slice.getMbAddrNAndLuma4x4BlkIdxN(xN, yN, maxW, maxH)
    #         if  mbAddrN == None or \
    #             (mbAddrN.mb_type.isInterProd() and self.bs.pps.constrained_intra_pred_flag) or \
    #             (self.slice.header.slice_type == SliceType.SI and self.bs.pps.constrained_intra_pred_flag) or \
    #             (x > 3 and (luma4x4BlkIdx == 3 or luma4x4BlkIdx == 11)):
    #             pass
    #         else:
    #             xM = InverseRasterScan(mbAddrN.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInSamplesL, 0)
    #             yM = InverseRasterScan(mbAddrN.CurrMbAddr, 16, 16, self.bs.sps.PicWidthInSamplesL, 1)
    #             P[x, y] = self.slice.lumaData.get(xM + xW, {}).get(yM + yW,0)

    #     self.Intra4x4predMode(luma4x4BlkIdx, isLuam, xO, yO, maxW, maxH)
    #     print(self.Intra4x4PredMode)


    # def Intra4x4predMode(self, luma4x4BlkIdx, isLuam:bool, x, y, maxW, maxH):
    #     '''
    #         4x4块预测模式推导
    #     '''
    #     mbAddrA, xW, yW = self.slice.getMbAddrNAndLuma4x4BlkIdxN(x-1, y, maxW, maxH)
    #     if mbAddrA != None:
    #         luma4x4BlkIdxA = 8 * (yW // 8) + 4 * (xW // 8) + 2 * ((yW % 8) // 4) + ((xW % 8) // 4)
    #     mbAddrB, xW, yW = self.slice.getMbAddrNAndLuma4x4BlkIdxN(x + 0, y + (-1), maxW, maxH)
    #     if mbAddrB != None:
    #         luma4x4BlkIdxB = 8 * (yW // 8) + 4 * (xW // 8) + 2 * ((yW % 8) // 4) + ((xW % 8) // 4)

    #     intraMxMPredModeA = None
    #     intraMxMPredModeB = None

    #     dcPredModePredictedFlag = 0
    #     if  mbAddrA == None or mbAddrB == None or \
    #         (mbAddrA != None and mbAddrA.mb_type.isInterProd() and self.bs.pps.constrained_intra_pred_flag) or \
    #         (mbAddrB != None and mbAddrB.mb_type.isInterProd() and self.bs.pps.constrained_intra_pred_flag):
    #         dcPredModePredictedFlag = 1

    #     if dcPredModePredictedFlag or \
    #         (mbAddrA != None and mbAddrA.mb_type.MbPartPredMode not in ("Intra_4x4", "Intra_8x8")): 
    #         intraMxMPredModeA = Intra4x4PredMode.Intra_4x4_DC
    #     else:
    #         # 根据左侧宏块的模式选择对应的预测模式
    #         if mbAddrA.mb_type.MbPartPredMode == "Intra_4x4":
    #             intraMxMPredModeA = mbAddrA.Intra4x4PredMode[luma4x4BlkIdxA]
    #         else:  # Intra_8x8
    #             intraMxMPredModeA = mbAddrA.Intra8x8PredMode[luma4x4BlkIdxA >> 2]

    #     # 处理上方相邻宏块的预测模式
    #     if dcPredModePredictedFlag or \
    #         (mbAddrB != None and mbAddrB.mb_type.MbPartPredMode not in ("Intra_4x4", "Intra_8x8")):
    #         intraMxMPredModeB = Intra4x4PredMode.Intra_4x4_DC
    #     else:
    #         # 根据上方宏块的模式选择对应的预测模式
    #         if mbAddrB.mb_type.MbPartPredMode == "Intra_4x4":
    #             intraMxMPredModeB = mbAddrB.Intra4x4PredMode[luma4x4BlkIdxB]
    #         else:  # Intra_8x8
    #             intraMxMPredModeB = mbAddrB.Intra8x8PredMode[luma4x4BlkIdxB >> 2]

    #     # 从左侧和上方相邻块的预测模式中选取较小的一个作为预先定义模式
    #     predIntra4x4PredMode = min(intraMxMPredModeA, intraMxMPredModeB)

    #     # 判断当前块的预测模式
    #     if self.prev_intra4x4_pred_mode_flag[luma4x4BlkIdx]:
    #         # 如果标志位为 1，则使用预定义模式
    #         self.Intra4x4PredMode[luma4x4BlkIdx] = predIntra4x4PredMode
    #     else:
    #         # 根据 rem_intra4x4_pred_mode 决定预测模式
    #         # print("predIntra4x4PredMode", predIntra4x4PredMode,intraMxMPredModeA, intraMxMPredModeB )
    #         if self.rem_intra4x4_pred_mode[luma4x4BlkIdx] < predIntra4x4PredMode:
    #             self.Intra4x4PredMode[luma4x4BlkIdx] = self.rem_intra4x4_pred_mode[luma4x4BlkIdx]
    #         else:
    #             self.Intra4x4PredMode[luma4x4BlkIdx] = self.rem_intra4x4_pred_mode[luma4x4BlkIdx] + 1



