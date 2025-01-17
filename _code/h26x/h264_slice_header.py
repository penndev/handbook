
import math
from h264_bs import BitStream
from h264_define import NalUnitType, SliceType
from h264_pps import PPS
from h264_sps import SPS

class SliceHeader:

    def dec_ref_pic_marking(self, bs):
        if self.idr_pic_flag:
            self.no_output_of_prior_pics_flag = bs.read_bits(1)
            self.long_term_reference_flag = bs.read_bits(1)
        else:
            adaptive_ref_pic_marking_mode_flag = bs.read_bits(1)
            if adaptive_ref_pic_marking_mode_flag:
                while True:
                    self.memory_management_control_operation = bs.read_ue()
                    if self.memory_management_control_operation in [1, 3]:
                        self.difference_of_pic_nums_minus1 = bs.read_ue()
                    if self.memory_management_control_operation == 2:
                        self.long_term_pic_num = bs.read_ue()
                    if self.memory_management_control_operation in [3, 6]:
                        self.long_term_frame_idx = bs.read_ue()
                    if self.memory_management_control_operation == 4:
                        self.max_long_term_frame_idx_plus1 = bs.read_ue()
                    if self.memory_management_control_operation == 0:
                        break

    def pred_weight_table(self, bs:BitStream, sps:SPS):
        self.luma_log2_weight_denom = bs.read_ue()
        if sps.chroma_format_idc != 0:  # 读取色度权重的对数值
            self.chroma_log2_weight_denom = bs.read_ue()
        for i in range(self.num_ref_idx_l0_active_minus1 + 1):
            luma_weight_l0_flag = bs.read_bits(1)
            if luma_weight_l0_flag:
                self.luma_weight_l0[i] = bs.read_se()
                self.luma_offset_l0[i] = bs.read_se()
            if sps.chroma_array_type != 0:
                chroma_weight_l0_flag = bs.read_bits(1)
                if chroma_weight_l0_flag:
                    for j in range(2):
                        self.chroma_weight_l0[i][j] = bs.read_se()
                        self.chroma_offset_l0[i][j] = bs.read_se()
        if self.slice_type % 5 == 1:
            # 处理 L1 引用帧的权重和偏移
            for i in range(self.num_ref_idx_l1_active_minus1 + 1):
                luma_weight_l1_flag = bs.read_bits(1)
                if luma_weight_l1_flag:
                    self.luma_weight_l1[i] = bs.read_se()
                    self.luma_offset_l1[i] = bs.read_se()

                if self.chroma_array_type != 0:
                    chroma_weight_l1_flag = bs.read_bits(1)
                    if chroma_weight_l1_flag:
                        for j in range(2):
                            self.chroma_weight_l1[i][j] = bs.read_se()
                            self.chroma_offset_l1[i][j] = bs.read_se()

    def ref_pic_list_modification(self, bs:BitStream):
        if self.slice_type % 5 != 2 and self.slice_type % 5 != 4:
            # 读取 ref_pic_list_modification_flag_l0
            self.ref_pic_list_modification_flag_l0 = bs.read_bits(1)
            if self.ref_pic_list_modification_flag_l0:
                # 循环解析 modification_of_pic_nums_idc
                while True:
                    modification_of_pic_nums_idc = bs.read_ue()
                    if modification_of_pic_nums_idc == 0 or modification_of_pic_nums_idc == 1:
                        self.abs_diff_pic_num_minus1 = bs.read_ue()
                    elif modification_of_pic_nums_idc == 2:
                        self.long_term_pic_num = bs.read_ue()
                    elif modification_of_pic_nums_idc == 3:
                        break  # 退出循环
        if self.slice_type % 5 == 1:  # 如果 slice_type 是 B 类型，需要处理 ref_pic_list_modification_flag_l1
            self.ref_pic_list_modification_flag_l1 = bs.read_bits(1)
            if self.ref_pic_list_modification_flag_l1:
                while True:
                    modification_of_pic_nums_idc = bs.read_ue()
                    if modification_of_pic_nums_idc == 0 or modification_of_pic_nums_idc == 1:
                        self.abs_diff_pic_num_minus1 = bs.read_ue()
                    elif modification_of_pic_nums_idc == 2:
                        self.long_term_pic_num = bs.read_ue()
                    elif modification_of_pic_nums_idc == 3:
                        break  # 退出循环


    def __init__(self, bs:BitStream, sps:SPS, pps:PPS, nal_unit_type:int, nal_ref_idc:int):
        self.idr_pic_flag = 1 if nal_unit_type == NalUnitType.IDR else 0

        self.first_mb_in_slice = bs.read_ue()
        '这个属性表示的是在这个 Slice 中第一个宏块的序号'
        self.slice_type = bs.read_ue() % 5
        '这个属性表示的是当前 Slice 的类型'
        self.pic_parameter_set_id = bs.read_ue()
        if self.pic_parameter_set_id != pps.pic_parameter_set_id:
            raise ValueError("pps id 不匹配")
        if sps.separate_colour_plane_flag:
            self.colour_plane_id = bs.read_bits(2)
            '这个属性表示的是当前 Slice 的颜色平面'
        self.frame_num = bs.read_bits(sps.log2_max_frame_num_minus4 + 4)
        '这个属性表示的是当前 Slice 的帧号'
        self.field_pic_flag = 0



        if not sps.frame_mbs_only_flag:
            self.field_pic_flag = bs.read_bits(1)
            '这个属性表示的是当前 Slice 是否是场帧'
            if self.field_pic_flag:
                self.bottom_field_flag = bs.read_bits(1)
                '这个属性表示的是当前 Slice 是否是底场'
        if self.idr_pic_flag:
            self.idr_pic_id = bs.read_ue()
            '这个属性表示的是当前 Slice 的 IDR 图像的 ID'
        if sps.pic_order_cnt_type == 0:
            self.pic_order_cnt_lsb = bs.read_bits(sps.log2_max_pic_order_cnt_lsb_minus4 + 4)
            '这个属性表示的是当前 Slice 的图像顺序计数器的 LSB'
            if pps.bottom_field_pic_order_in_frame_present_flag and not getattr(self, 'field_pic_flag', False):
                self.delta_pic_order_cnt_bottom = bs.read_se()
        if sps.pic_order_cnt_type == 1 and not sps.delta_pic_order_always_zero_flag:
            self.delta_pic_order_cnt_0 = bs.read_se()
            if pps.bottom_field_pic_order_in_frame_present_flag and not getattr(self, 'field_pic_flag', False):
                self.delta_pic_order_cnt_1 = bs.read_se()
        if pps.redundant_pic_cnt_present_flag:
            self.redundant_pic_cnt = bs.read_ue()
        if self.slice_type == SliceType.B:
            self.direct_spatial_mv_pred_flag = bs.read_bits(1)
        if self.slice_type in [SliceType.P, SliceType.SP, SliceType.B]:
            self.num_ref_idx_active_override_flag = bs.read_bits(1)
            if self.num_ref_idx_active_override_flag:
                self.num_ref_idx_l0_active_minus1 = bs.read_ue()
                if self.slice_type == SliceType.B:
                    self.num_ref_idx_l1_active_minus1 = bs.read_ue()
        if nal_unit_type in (20,21):
            raise ValueError("未支持的帧类型")
        else:
            self.ref_pic_list_modification(bs)
        if (pps.weighted_pred_flag == 1 and self.slice_type in [SliceType.P, SliceType.SP]) or \
           (pps.weighted_bipred_idc == 1 and self.slice_type == SliceType.B):  # pred_weight_table
            self.pred_weight_table(bs)
        if nal_ref_idc != 0:  # dec_ref_pic_marking
            self.dec_ref_pic_marking(bs)
        if pps.entropy_coding_mode_flag and self.slice_type not in [SliceType.I, SliceType.SI]:
            self.cabac_init_idc = bs.read_ue()
            '这个属性表示的是 CABAC 初始化的上下文模型'
        self.slice_qp_delta = bs.read_se()
        self.SliceQPY = 26 + pps.pic_init_qp_minus26 + self.slice_qp_delta
        '''这个属性表示的是当前 Slice 的量化参数，这个值是由 PPS 中的 pic_init_qp_minus26 和当前 Slice 的 slice_qp_delta 计算得到的'''
        self.slice_qs_delta = 0
        if self.slice_type in [SliceType.SP, SliceType.SI]:
            if self.slice_type == SliceType.SP:
                self.sp_for_switch_flag = bs.read_bits(1)
            self.slice_qs_delta = bs.read_se()
        
        if pps.deblocking_filter_control_present_flag:
            self.disable_deblocking_filter_idc = bs.read_ue()
            if self.disable_deblocking_filter_idc != 1:
                self.slice_alpha_c0_offset_div2 = bs.read_se()
                self.slice_beta_offset_div2 = bs.read_se()
        if pps.num_slice_groups_minus1 > 0 and 3 <= pps.slice_group_map_type <= 5:
            pic_size = (sps.pic_width_in_mbs_minus1 + 1) * (sps.pic_height_in_map_units_minus1 + 1)
            max = (pic_size + pps.slice_group_change_rate_minus1) // (pps.slice_group_change_rate_minus1 + 1)
            self.slice_group_change_cycle = bs.read_bits(math.ceil(math.log2(max + 1)))


        # 逻辑变量
        self.MbaffFrameFlag = 1 if sps.mb_adaptive_frame_field_flag and not self.field_pic_flag else 0

        self.PicHeightInMbs = bs.sps.FrameHeightInMbs / ( 1 + self.field_pic_flag ) 
        self.PicSizeInMbs = bs.sps.PicWidthInMbs * self.PicHeightInMbs

        self.PicHeightInSamplesL = self.PicHeightInMbs * 16

        # //QSY 的值用于解码 mb_type 等SI 的SI 条带的所有宏块以及预测模式为帧间的SP 条带的所有宏块。
        self.QSY = 26 + pps.pic_init_qs_minus26 + self.slice_qs_delta
        
        
        self.ScalingList4x4 = {}
        self.ScalingList8x8 = {}
        if not sps.seq_scaling_matrix_present_flag and not pps.pic_scaling_matrix_present_flag:
            for i in range(12) :
                if i < 6:
                    self.ScalingList4x4[i] = {i: 16 for i in range(16)}
                else:
                    self.ScalingList8x8[i] = {i: 16 for i in range(64)}
        if sps.seq_scaling_matrix_present_flag:
            self.ScalingList4x4, self.ScalingList8x8 = sps.ScalingList4x4, sps.ScalingList8x8
        if pps.pic_scaling_matrix_present_flag:
            self.ScalingList4x4, self.ScalingList8x8 = pps.ScalingList4x4, pps.ScalingList8x8