'CODE logic from <T-REC-H.264-202108-I!!PDF-E.pdf>'
from enum import Enum
import json
import math
from typing import Generator

class SliceType(Enum):
    '''Table 7-6  Name association to slice_type'''
    P = 0
    B = 1
    I = 2 
    SP = 3
    SI = 4

    def __eq__(self, other):
        if isinstance(other, int):
            return self.value == other % 5
        return False

class BitStream():
    '''根据 7.2 Specification of syntax functions, categories, and descriptors 文档定义的数据读取方法'''
    def __init__(self, hex:bytearray) -> None:
        self.hex = hex
        self.position = 0
    def read_bits(self, n) -> int:
        '从字节流 返回n位无符号整数 大字节序列'
        value = 0  # 用于存储读取的值
        while n > 0:
            byte_pos = self.position // 8  # 当前字节的位置
            bit_offset = self.position % 8  # 当前字节的位偏移量
            remaining_bits_in_byte = 8 - bit_offset # 当前字节剩余可用位数
            bits_to_read = min(n, remaining_bits_in_byte) # 计算当前读取的位数，取 n 和剩余位数的最小值
            current_byte = self.hex[byte_pos]  # 从当前字节提取所需的位
            current_bits = (current_byte >> (remaining_bits_in_byte - bits_to_read)) & ((1 << bits_to_read) - 1)
            value = (value << bits_to_read) | current_bits # 将提取到的位拼接到结果中
            self.position += bits_to_read  # 更新位置和剩余要读取的位数
            n -= bits_to_read
        return value
    def read_ue(self) -> int:
        '''解析 H.264 中的 ue(v) (无符号指数哥伦布编码0阶)'''
        leading_zeros = 0
        while self.read_bits(1) == 0: # 1. 计算前导零的个数
            leading_zeros += 1
        if leading_zeros == 0: # 2. 读取对应数量的位
            return 0  # 特殊情况，前导 0 个数为 0 时，值为 0
        return (1 << leading_zeros) - 1 + self.read_bits(leading_zeros)
    def read_se(self) -> int:
        code_num = self.read_ue()
        if code_num % 2 == 0:
            return -(code_num // 2) 
        else:
            return code_num // 2 + 1 
    def more_rbsp_data(self):
        return self.position / 8 + 2 > len(self.hex)
    

class NAL():
    '7 单元结构体的实现'

    def dec_ref_pic_marking(self):
        if self.idr_pic_flag:
            self.no_output_of_prior_pics_flag = self.stream.read_bits(1)
            self.long_term_reference_flag = self.stream.read_bits(1)
        else:
            adaptive_ref_pic_marking_mode_flag = self.stream.read_bits(1)
            if adaptive_ref_pic_marking_mode_flag:
                while True:
                    self.memory_management_control_operation = self.read_ue()
                    if self.memory_management_control_operation in [1, 3]:
                        self.difference_of_pic_nums_minus1 = self.read_ue()
                    if self.memory_management_control_operation == 2:
                        self.long_term_pic_num = self.read_ue()
                    if self.memory_management_control_operation in [3, 6]:
                        self.long_term_frame_idx = self.read_ue()
                    if self.memory_management_control_operation == 4:
                        self.max_long_term_frame_idx_plus1 = self.read_ue()
                    if self.memory_management_control_operation == 0:
                        break

    def pred_weight_table(self):
        self.luma_log2_weight_denom = self.stream.read_ue()
        
        if self.sps.chroma_format_idc != 0: # 读取色度权重的对数值
            self.chroma_log2_weight_denom = self.stream.read_ue()
        for i in range(self.num_ref_idx_l0_active_minus1 + 1):
            luma_weight_l0_flag = self.stream.read_bits(1)
            if luma_weight_l0_flag:
                self.luma_weight_l0[i] = self.stream.read_se()
                self.luma_offset_l0[i] = self.stream.read_se()
            if self.sps.chroma_array_type != 0:
                chroma_weight_l0_flag = self.stream.read_bits(1)
                if chroma_weight_l0_flag:
                    for j in range(2):
                        self.chroma_weight_l0[i][j] = self.read_se()
                        self.chroma_offset_l0[i][j] = self.read_se()
        if self.slice_type % 5 == 1:
            # 处理 L1 引用帧的权重和偏移
            for i in range(self.num_ref_idx_l1_active_minus1 + 1):
                luma_weight_l1_flag = self.stream.read_bits(1)
                if luma_weight_l1_flag:
                    self.luma_weight_l1[i] = self.read_se()
                    self.luma_offset_l1[i] = self.read_se()

                if self.chroma_array_type != 0:
                    chroma_weight_l1_flag = self.stream.read_bits(1)
                    if chroma_weight_l1_flag:
                        for j in range(2):
                            self.chroma_weight_l1[i][j] = self.read_se()
                            self.chroma_offset_l1[i][j] = self.read_se()

    def ref_pic_list_modification(self):
        if self.slice_type % 5 != 2 and self.slice_type % 5 != 4:
            # 读取 ref_pic_list_modification_flag_l0
            self.ref_pic_list_modification_flag_l0 = self.stream.read_bits(1)
            if self.ref_pic_list_modification_flag_l0:
                # 循环解析 modification_of_pic_nums_idc
                while True:
                    modification_of_pic_nums_idc = self.stream.read_ue()
                    if modification_of_pic_nums_idc == 0 or modification_of_pic_nums_idc == 1:
                        self.abs_diff_pic_num_minus1 = self.stream.read_ue()
                    elif modification_of_pic_nums_idc == 2:
                        self.long_term_pic_num = self.stream.read_ue()
                    elif modification_of_pic_nums_idc == 3:
                        break  # 退出循环
        if self.slice_type  % 5 == 1:  # 如果 slice_type 是 B 类型，需要处理 ref_pic_list_modification_flag_l1
            self.ref_pic_list_modification_flag_l1 = self.stream.read_bits(1)
            if self.ref_pic_list_modification_flag_l1:
                while True:
                    modification_of_pic_nums_idc = self.stream.read_ue()
                    if modification_of_pic_nums_idc == 0 or modification_of_pic_nums_idc == 1:
                        self.abs_diff_pic_num_minus1 = self.stream.read_ue()
                    elif modification_of_pic_nums_idc == 2:
                        self.long_term_pic_num = self.stream.read_ue()
                    elif modification_of_pic_nums_idc == 3:
                        break  # 退出循环

    def slice_header(self):
        self.idr_pic_flag = 1 if self.nal_unit_type == 5 else 0
        self.first_mb_in_slice = self.stream.read_ue()
        self.slice_type = self.stream.read_ue()
        self.pic_parameter_set_id = self.stream.read_ue()
        if self.sps.separate_colour_plane_flag:
            self.colour_plane_id = self.stream.read_bits(2)
        self.frame_num = self.stream.read_bits(self.sps.log2_max_frame_num_minus4 + 4)
        if not self.sps.frame_mbs_only_flag:
            self.field_pic_flag = self.stream.read_bits(1)
            if self.field_pic_flag:
                self.bottom_field_flag = self.stream.read_bits(1)
        if self.idr_pic_flag:
            self.idr_pic_id = self.stream.read_ue()
        if self.sps.pic_order_cnt_type == 0:
            self.pic_order_cnt_lsb = self.stream.read_bits(self.sps.log2_max_pic_order_cnt_lsb_minus4 + 4)
            if self.pps.bottom_field_pic_order_in_frame_present_flag and not getattr(self, 'field_pic_flag', False):
                self.delta_pic_order_cnt_bottom = self.stream.read_se()
        if self.sps.pic_order_cnt_type == 1 and not self.delta_pic_order_always_zero_flag:
            self.delta_pic_order_cnt_0 = self.stream.read_se()
            if self.pps.bottom_field_pic_order_in_frame_present_flag and not getattr(self, 'field_pic_flag', False):
                self.delta_pic_order_cnt_1 = self.stream.read_se()
        if self.pps.redundant_pic_cnt_present_flag:
            self.redundant_pic_cnt = self.stream.read_ue()
        if self.slice_type == SliceType.B:
            self.direct_spatial_mv_pred_flag = self.stream.read_bits(1)
        if self.slice_type in [SliceType.P, SliceType.SP, SliceType.B]:
            self.num_ref_idx_active_override_flag = self.stream.read_bits(1)
            if self.num_ref_idx_active_override_flag:
                self.num_ref_idx_l0_active_minus1 = self.stream.read_ue()
                if self.slice_type == SliceType.B:
                    self.num_ref_idx_l1_active_minus1 = self.stream.read_ue()
        if self.nal_unit_type in [20, 21]:  # ref_pic_list_mvc_modification
            self.ref_pic_list_mvc_modification()
        else:  # ref_pic_list_modification
            self.ref_pic_list_modification()
        if (self.pps.weighted_pred_flag and self.slice_type in [SliceType.P, SliceType.SP]) or \
           (self.pps.weighted_bipred_idc == 1 and self.slice_type == SliceType.B):  # pred_weight_table
            self.pred_weight_table()
        if self.nal_ref_idc != 0:  # dec_ref_pic_marking
            self.dec_ref_pic_marking()
        if self.pps.entropy_coding_mode_flag and self.slice_type not in [SliceType.I, SliceType.SI]:
            self.cabac_init_idc = self.stream.read_ue()
        self.slice_qp_delta = self.stream.read_se()
        if self.slice_type in [SliceType.SP, SliceType.SI]:
            if self.slice_type == SliceType.SP:
                self.sp_for_switch_flag = self.stream.read_bits(1)
            self.slice_qs_delta = self.stream.read_se()
        if self.pps.deblocking_filter_control_present_flag:
            self.disable_deblocking_filter_idc = self.stream.read_ue()
            if self.disable_deblocking_filter_idc != 1:
                self.slice_alpha_c0_offset_div2 = self.stream.read_se()
                self.slice_beta_offset_div2 = self.stream.read_se()
        if self.pps.num_slice_groups_minus1 > 0 and 3 <= self.pps.slice_group_map_type <= 5:
            pic_size = (self.sps.pic_width_in_mbs_minus1 + 1) * (self.sps.pic_height_in_map_units_minus1 + 1)
            max = (pic_size + self.pps.slice_group_change_rate_minus1) // (self.pps.slice_group_change_rate_minus1 + 1) 
            self.slice_group_change_cycle = self.stream.read_bits(math.ceil(math.log2(max + 1))) 

    def slice_data(self):
        if self.pps.entropy_coding_mode_flag :
            while self.stream.position % 8 != 0:
                self.stream.read_bits(1)
        
        MbaffFrameFlag = getattr(self.sps, "mb_adaptive_frame_field_flag", False) and self.field_pic_flag
        # 当前宏块地址。
        self.CurrMbAddr = self.first_mb_in_slice * (1 + MbaffFrameFlag)

        moreDataFlag = 1
        prevMbSkipped = 0

        condition = True
        while condition:
            if self.slice_type not in [SliceType.I, SliceType.SI ]:
                # if not self.pps.entropy_coding_mode_flag:
                #     self.mb_skip_run = self.stream.read_ue()
                #     self.prevMbSkipped = ( self.mb_skip_run > 0 ) 
                #     raise("计算下一个宏块的地址")
                #     # 没懂。
                #     # for( i=0; i<mb_skip_run; i++ )
                #     #     CurrMbAddr = NextMbAddress( CurrMbAddr )
                #     # moreDataFlag = more_rbsp_data( ) 
                # else:
                #     # " 9-13
                #     # " 9-14
                #     # self.mb_skip_flag = self.stream.read_ae()
                #     pass
                raise("SliceType" + self.slice_type)


    def pic_parameter_set_rbsp(self):
        self.pic_parameter_set_id = self.stream.read_ue()
        self.seq_parameter_set_id = self.stream.read_ue()
        self.entropy_coding_mode_flag = self.stream.read_bits(1)
        self.bottom_field_pic_order_in_frame_present_flag = self.stream.read_bits(1)
        self.num_slice_groups_minus1 = self.stream.read_ue()
        if self.num_slice_groups_minus1 > 0:
            self.slice_group_map_type = self.stream.read_ue()
            if self.slice_group_map_type == 0:
                self.run_length_minus1 = [self.stream.read_ue() for _ in range(self.num_slice_groups_minus1 + 1)]
            elif self.slice_group_map_type == 2:
                self.top_left = [self.stream.read_ue() for _ in range(self.num_slice_groups_minus1)]
                self.bottom_right = [self.stream.read_ue() for _ in range(self.num_slice_groups_minus1)]
            elif self.slice_group_map_type in {3, 4, 5}:
                self.slice_group_change_direction_flag = self.stream.read_bits(1)
                self.slice_group_change_rate_minus1 = self.stream.read_ue()
            elif self.slice_group_map_type == 6:
                self.pic_size_in_map_units_minus1 = self.stream.read_ue()
                self.slice_group_id = [self.stream.read_bits(1) for _ in range(self.pic_size_in_map_units_minus1 + 1)]
        # 解析默认活动参考帧数
        self.num_ref_idx_l0_default_active_minus1 = self.stream.read_ue()
        self.num_ref_idx_l1_default_active_minus1 = self.stream.read_ue()
        # 解析加权预测相关参数
        self.weighted_pred_flag = self.stream.read_bits(1)
        self.weighted_bipred_idc = self.stream.read_bits(2)
        # 解析量化参数
        self.pic_init_qp_minus26 = self.stream.read_se()
        self.pic_init_qs_minus26 = self.stream.read_se()
        self.chroma_qp_index_offset = self.stream.read_se()
        # 解析去块滤波相关标志
        self.deblocking_filter_control_present_flag = self.stream.read_bits(1)
        self.constrained_intra_pred_flag = self.stream.read_bits(1)
        self.redundant_pic_cnt_present_flag = self.stream.read_bits(1)
        # 如果有更多的 RBSP 数据
        if self.stream.more_rbsp_data():
            self.transform_8x8_mode_flag = self.stream.read_bits(1)
            self.pic_scaling_matrix_present_flag = self.stream.read_bits(1)
            if self.pic_scaling_matrix_present_flag:
                pic_scaling_list_present_flag = []
                # scaling_list = []
                for i in range(6 + ((self.sps.chroma_format_idc != 3) * 2) * self.transform_8x8_mode_flag):
                    pic_scaling_list_present_flag.append(self.stream.read_bits(1))
                    if pic_scaling_list_present_flag[i]:
                        pass
                        # if i < 6:
                        #     scaling_list.append(self.scaling_list(ScalingList4x4[i], 16, UseDefaultScalingMatrix4x4Flag[i]))
                        # else:
                        #     scaling_list.append(self.scaling_list(ScalingList8x8[i - 6], 64, UseDefaultScalingMatrix8x8Flag[i - 6]))
                # self.pic_scaling_list_present_flag = pic_scaling_list_present_flag
                # self.scaling_list = scaling_list
            self.second_chroma_qp_index_offset = self.stream.read_se()

    def hrd_parameters(self):
        self.cpb_cnt_minus1 = self.stream.read_ue()
        self.bit_rate_scale = self.stream.read_bits(4)
        self.cpb_size_scale = self.stream.read_bits(4)
        self.bit_rate_value_minus1 = []
        self.cpb_size_value_minus1 = []
        self.cbr_flag = []
        for _ in range(self.cpb_cnt_minus1 + 1):
            self.bit_rate_value_minus1.append(self.stream.read_uev())
            self.cpb_size_value_minus1.append(self.stream.read_uev())
            self.cbr_flag.append(self.stream.read_bits(1))
        self.initial_cpb_removal_delay_length_minus1 = self.stream.read_bits(5)
        self.cpb_removal_delay_length_minus1 = self.stream.read_bits(5)
        self.dpb_output_delay_length_minus1 = self.stream.read_bits(5)
        self.time_offset_length = self.stream.read_bits(5)

    def vui_parameters(self):
        self.aspect_ratio_info_present_flag = self.stream.read_bits(1)
        if self.aspect_ratio_info_present_flag:
            self.aspect_ratio_idc = self.stream.read_bits(8)
            if self.aspect_ratio_idc == 255:  # Extended_SAR, typically denoted as 255
                self.sar_width = self.stream.read_bits(16)
                self.sar_height = self.stream.read_bits(16)
        self.overscan_info_present_flag = self.stream.read_bits(1)
        if self.overscan_info_present_flag:
            self.overscan_appropriate_flag = self.stream.read_bits(1)
        self.video_signal_type_present_flag = self.stream.read_bits(1)
        if self.video_signal_type_present_flag:
            self.video_format = self.stream.read_bits(3)
            self.video_full_range_flag = self.stream.read_bits(1)
            self.colour_description_present_flag = self.stream.read_bits(1)
            if self.colour_description_present_flag:
                self.colour_primaries = self.stream.read_bits(8)
                self.transfer_characteristics = self.stream.read_bits(8)
                self.matrix_coefficients = self.stream.read_bits(8)
        self.chroma_loc_info_present_flag = self.stream.read_bits(1)
        if self.chroma_loc_info_present_flag:
            self.chroma_sample_loc_type_top_field = self.stream.read_ue()  # Exp-Golomb-coded value (ue(v))
            self.chroma_sample_loc_type_bottom_field = self.stream.read_ue()  # Exp-Golomb-coded value (ue(v))
        self.timing_info_present_flag = self.stream.read_bits(1)
        if self.timing_info_present_flag:
            self.num_units_in_tick = self.stream.read_bits(32)
            self.time_scale = self.stream.read_bits(32)
            self.fixed_frame_rate_flag = self.stream.read_bits(1)

        self.nal_hrd_parameters_present_flag = self.stream.read_bits(1)
        if self.nal_hrd_parameters_present_flag:
            self.hrd_parameters()  # NAL HRD parameters

        self.vcl_hrd_parameters_present_flag = self.stream.read_bits(1)
        if self.vcl_hrd_parameters_present_flag:
            self.hrd_parameters()  # VCL HRD parameters

        if self.nal_hrd_parameters_present_flag or self.vcl_hrd_parameters_present_flag:
            self.low_delay_hrd_flag = self.stream.read_bits(1)

        self.pic_struct_present_flag = self.stream.read_bits(1)
        self.bitstream_restriction_flag = self.stream.read_bits(1)

        if self.bitstream_restriction_flag:
            self.motion_vectors_over_pic_boundaries_flag = self.stream.read_bits(1)
            self.max_bytes_per_pic_denom = self.stream.read_ue()
            self.max_bits_per_mb_denom = self.stream.read_ue()
            self.log2_max_mv_length_horizontal = self.stream.read_ue()
            self.log2_max_mv_length_vertical = self.stream.read_ue()
            self.max_num_reorder_frames = self.stream.read_ue()
            self.max_dec_frame_buffering = self.stream.read_ue()

    def seq_parameter_set_data(self):
        self.profile_idc = self.stream.read_bits(8)
        self.constraint_set0_flag = self.stream.read_bits(1)
        self.constraint_set1_flag = self.stream.read_bits(1)
        self.constraint_set2_flag = self.stream.read_bits(1)
        self.constraint_set3_flag = self.stream.read_bits(1)
        self.reserved_zero_4bits = self.stream.read_bits(4)
        self.level_idc = self.stream.read_bits(8)
        self.seq_parameter_set_id = self.stream.read_ue()
        self.separate_colour_plane_flag = 0
        self.log2_max_frame_num_minus4 = 0
        self.frame_mbs_only_flag = 0
        self.pic_order_cnt_type = 0
        if self.profile_idc in (100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135):
            self.chroma_format_idc = self.stream.read_ue()
            if self.chroma_format_idc == 3:
                self.separate_colour_plane_flag = self.stream.read_bits(1)
            self.bit_depth_luma_minus8 = self.stream.read_ue()
            self.bit_depth_chroma_minus8 = self.stream.read_ue()
            self.qpprime_y_zero_transform_bypass_flag = self.stream.read_bits(1)
            self.seq_scaling_matrix_present_flag = self.stream.read_bits(1)
            if self.seq_scaling_matrix_present_flag == 1:
                for i in range(8 if self.chroma_format_idc != 3 else 12):
                    # seq_scaling_list_present_flag
                    self.stream.read_bits(1)
                    # UseDefaultScalingMatrix4x4Flag
            self.log2_max_frame_num_minus4 = self.stream.read_ue()
            self.pic_order_cnt_type = self.stream.read_ue()
            if self.pic_order_cnt_type == 0:
                self.log2_max_pic_order_cnt_lsb_minus4 = self.stream.read_ue()
            elif self.pic_order_cnt_type == 1:
                self.delta_pic_order_always_zero_flag = self.stream.read_bits(1)
                self.offset_for_non_ref_pic = self.stream.read_ue()
                self.offset_for_top_to_bottom_field = self.stream.read_ue()
                self.num_ref_frames_in_pic_order_cnt_cycle = self.stream.read_ue()
                for i in range(self.num_ref_frames_in_pic_order_cnt_cycle):
                    # offset_for_ref_frame[i]
                    self.stream.read_se()
            self.num_ref_frames = self.stream.read_ue()
            self.gaps_in_frame_num_value_allowed_flag = self.stream.read_bits(1)
            self.pic_width_in_mbs_minus1 = self.stream.read_ue()
            self.pic_height_in_map_units_minus1 = self.stream.read_ue()
            self.frame_mbs_only_flag = self.stream.read_bits(1)
            if self.frame_mbs_only_flag != 1:
                self.mb_adaptive_frame_field_flag = self.stream.read_bits(1)
            self.direct_8x8_inference_flag = self.stream.read_bits(1)
            self.frame_cropping_flag = self.stream.read_bits(1)
            if self.frame_cropping_flag == 1:
                self.frame_crop_left_offset = self.stream.read_ue()
                self.frame_crop_right_offset = self.stream.read_ue()
                self.frame_crop_top_offset = self.stream.read_ue()
                self.frame_crop_bottom_offset = self.stream.read_ue()
            self.vui_parameters_present_flag = self.stream.read_bits(1)
            if self.vui_parameters_present_flag == 1:
                self.vui_parameters()

    def __init__(self, hex:bytearray, sps, pps):
        
        self.sps = sps
        self.pps = pps
        self.stream = BitStream(hex)

        self.forbidden_zero_bit = self.stream.read_bits(1)
        self.nal_ref_idc = self.stream.read_bits(2)
        self.nal_unit_type = self.stream.read_bits(5)
        'Table 7-1 – NAL unit type codes, syntax element categories, and NAL unit type classes'
        if self.nal_unit_type in (1, 5, 19): #slice_layer_without_partitioning_rbsp()
            self.slice_header()
            self.slice_data()
        elif self.nal_unit_type == 7: #sps  seq_parameter_set_rbsp() 
            self.seq_parameter_set_data()
            # rbsp_trailing_bits() 本身已做了 nal unit so 不需要处理剩下的几个bit数据
        elif self.nal_unit_type == 8: #pps 
            self.pic_parameter_set_rbsp()
        elif self.nal_unit_type in (14, 20, 21):
            raise('NO 3D SUPPORT')
        print(json.dumps(self.to_dict(), indent=4))

    def to_dict(self):
        attributes = self.__dict__.copy()
        # name = 'stream'
        # if name in attributes:
        #     del attributes[name]
        # name = 'sps'
        # if name in attributes:
        #     del attributes[name]
        del attributes["sps"]
        del attributes["pps"]
        del attributes["stream"]
        return attributes


class H264(): 
    '''
    B.1 Byte stream NAL unit syntax and semantics
    '''
    def nal_unit(self, hex):
        if len(hex) == 0: # 头字节引起
            return
        nal = NAL(hex, sps = self.sps_nalu, pps= self.pps_nalu)
        if nal.nal_unit_type == 7:
            self.sps_nalu = nal
        if nal.nal_unit_type == 8:
            self.pps_nalu = nal

    def read_h264(self) -> Generator[bytearray, None, None] :
        with open(self.filename, "rb") as f:
            while chunk := f.read(self.chunk_size):
                yield bytearray(chunk)  # 每次读取一块并返回

    def __init__(self,filename):
        self.sps_nalu = None
        self.pps_nalu = None

        self.hex = bytearray()
        'filename 输入文件必须是h264文件'
        self.filename = filename
        self.chunk_size = 1024
        # 开始分割
        current_nal_unit = bytearray()
        last_hex = bytearray()
        for hex in self.read_h264():
            if len(last_hex):
                hex = last_hex + hex
            current_nal_unit_start_position = 0
            readCounter = 0
            hexLen = len(hex) - 2
            while hexLen > readCounter:
                if hex[readCounter] != 0:
                    readCounter += 1
                    continue
                if hex[readCounter+1] != 0:
                    readCounter += 2
                    continue
                if hex[readCounter+2] == 0:
                    if hex[readCounter+3] == 1: # 0x00000001 分割。
                        # ======
                        current_nal_unit = current_nal_unit + hex[current_nal_unit_start_position:readCounter]
                        self.nal_unit(current_nal_unit)
                        current_nal_unit = bytearray()
                        # ======
                        readCounter += 4
                        current_nal_unit_start_position = readCounter
                        continue
                    else:
                        raise('NALU 0x000000 HIT!')
                elif hex[readCounter+2] == 1: # 0x000001 分割。
                    # ======
                    current_nal_unit = current_nal_unit + hex[current_nal_unit_start_position:readCounter]
                    self.nal_unit(current_nal_unit)
                    current_nal_unit = bytearray()
                    # ======
                    readCounter += 3
                    current_nal_unit_start_position = readCounter
                    continue
                # 7.4.1 NAL unit semantics
                elif hex[readCounter+2] == 2:
                    raise('NALU 0x000002 HIT!')
                elif hex[readCounter+2] == 3: # RBSP BODY filter 03 = SODB
                    del hex[readCounter+2] # //处理透明传输，进行00替换还原
                    hexLen -= 1 
                    readCounter += 2
                else:
                    readCounter += 3
                    
            # 类似处理tcp粘包
            if hex[readCounter + 1] != 0:
                last_hex = bytearray()
                current_nal_unit = current_nal_unit + hex[current_nal_unit_start_position:]
            else: 
                last_hex =  hex[readCounter:]
                current_nal_unit += hex[current_nal_unit_start_position: readCounter]
        current_nal_unit = current_nal_unit + last_hex
        self.nal_unit(current_nal_unit)

if __name__ == "__main__":
    nal = H264("runtime/output.h264")
    # FILE_OUT = open('rbsp.h264', "wb")
    # FILE_OUT.write(nal.hex)
