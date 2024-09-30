import math




class BitStream():
    def __init__(self, rbsp:bytearray) -> None:
        self.rbsp = rbsp
        self.position = 0
        return self
    def read_bit(self, n) -> int:
        '返回n位无符号整数'
        value = 0  # 用于存储读取的值
        while n > 0:
            byte_pos = self.position // 8  # 当前字节的位置
            bit_offset = self.position % 8  # 当前字节的位偏移量
            
            # 当前字节剩余可用位数
            remaining_bits_in_byte = 8 - bit_offset
            # 计算当前读取的位数，取 n 和剩余位数的最小值
            bits_to_read = min(n, remaining_bits_in_byte)
            
            # 从当前字节提取所需的位
            current_byte = self.rbsp[byte_pos]
            current_bits = (current_byte >> (remaining_bits_in_byte - bits_to_read)) & ((1 << bits_to_read) - 1)
            
            # 将提取到的位拼接到结果中
            value = (value << bits_to_read) | current_bits
            
            # 更新位置和剩余要读取的位数
            self.position += bits_to_read
            n -= bits_to_read
        return value
    def read_uev(self) -> int:
        '''解析 H.264 中的 ue(v) (无符号指数哥伦布编码0阶)'''
        leading_zeros = 0
        while self.read_bit(1) == 0: # 1. 计算前导零的个数
            leading_zeros += 1
        if leading_zeros == 0: # 2. 读取对应数量的位
            return 0  # 特殊情况，前导 0 个数为 0 时，值为 0
        return (1 << leading_zeros) - 1 + self.read_bit(leading_zeros)
    def read_sev(self) -> int:
        code_num = self.read_uev()
        if code_num % 2 == 0:
            return code_num // 2  # 正数
        else:
            return -(code_num // 2 + 1)  # 负数



class NAL(BitStream):
    
    SLICE_TYPE_P = 0
    SLICE_TYPE_B = 1
    SLICE_TYPE_I = 2
    SLICE_TYPE_SP = 3
    SLICE_TYPE_SI = 4
    @staticmethod
    def SLICE_TYPE(select_type):
        '''
        slice_type specifies the coding type of the slice according to Table 7-6.
        Table 7-6 – Name association to slice_type
        '''
        return select_type % 5 == 0 


    # 这个到底是什么还不知道。

    def __init__(self, hex:bytearray):
        self.forbidden_zero_bit = hex[0] >> 7 & 1
        self.nal_ref_idc = hex[0] >> 5 & 3
        self.nal_unit_type = hex[0] & 0x1f
        # 初始化字节流
        super().__init__(hex[1:])
        if self.nal_unit_type == 5: #idr
            self.slice_layer_without_partitioning_rbsp()
        if self.nal_unit_type == 7: #sps
            self.seq_parameter_set_rbsp()
        if self.nal_unit_type == 8: #pps
            self.pic_parameter_set_rbsp()
    
    log2_max_frame_num_minus4 = None
    frame_mbs_only_flag = None
    pic_order_cnt_type = None
    log2_max_pic_order_cnt_lsb_minus4 = None
    delta_pic_order_always_zero_flag = None
    chroma_format_idc = None
    def seq_parameter_set_rbsp(self):
        profile_idc = self.read_bit(8)
        constraint_set0_flag = self.read_bit(1)
        constraint_set1_flag = self.read_bit(1)
        constraint_set2_flag = self.read_bit(1)
        constraint_set3_flag = self.read_bit(1)
        reserved_zero_4bits = self.read_bit(4)
        level_idc = self.read_bit(8)
        seq_parameter_set_id = self.read_uev()
        if profile_idc in (100, 110, 122, 144): 
            self.chroma_format_idc = self.read_uev()
            if self.chroma_format_idc == 3:
                residual_colour_transform_flag = self.read_bit(1)
            bit_depth_luma_minus8 = self.read_uev()
            bit_depth_chroma_minus8 = self.read_uev()
            qpprime_y_zero_transform_bypass_flag = self.read_bit(1)
            seq_scaling_matrix_present_flag = self.read_bit(1)
            if seq_scaling_matrix_present_flag == 1:
                for i in range(8):
                    # seq_scaling_list_present_flag[i]
                    if self.read_bit(1) == 1:
                        pass 
                        # if i < 6 : 这里是给p b帧率用的。
                        #     scaling_list( 
                        #         ScalingList4x4[ i ], 
                        #         16, 
                        #         UseDefaultScalingMatrix4x4Flag[ i ]
                        #     )
                        # else: 
                        #     scaling_list( ScalingList8x8[ i – 6 ], 64,
                        #     UseDefaultScalingMatrix8x8Flag[ i – 6 ] ) 
        NAL.log2_max_frame_num_minus4 = self.read_uev()
        NAL.pic_order_cnt_type = self.read_uev()
        if NAL.pic_order_cnt_type == 0:
            NAL.log2_max_pic_order_cnt_lsb_minus4 = self.read_uev()
        elif NAL.pic_order_cnt_type == 1:
            NAL.delta_pic_order_always_zero_flag = self.read_bit(1)
            offset_for_non_ref_pic  = self.read_sev()
            offset_for_top_to_bottom_field = self.read_sev()
            num_ref_frames_in_pic_order_cnt_cycle  = self.read_uev()
            for i in range(num_ref_frames_in_pic_order_cnt_cycle): 
                self.read_sev()
                # offset_for_ref_frame[i]
                #
        num_ref_frames = self.read_uev()
        gaps_in_frame_num_value_allowed_flag = self.read_bit(1)
        pic_width_in_mbs_minus1 = self.read_uev()
        pic_height_in_map_units_minus1 = self.read_uev()
        NAL.frame_mbs_only_flag = self.read_bit(1)
        # 其他数据了，数据也太多太麻烦了把。。。
        # print(profile_idc,
        #       level_idc,
        #       seq_parameter_set_id,
        #       bit_depth_chroma_minus8,
        #       log2_max_frame_num_minus4,
        #       num_ref_frames,
        #       pic_width_in_mbs_minus1,
        #       pic_height_in_map_units_minus1
        #       )
    
    pic_order_present_flag = None
    redundant_pic_cnt_present_flag = None
    weighted_pred_flag = None
    weighted_bipred_idc = None
    num_ref_idx_l0_active_minus1 = None
    def pic_parameter_set_rbsp(self):
        '7.3.2.2'
        pic_parameter_set_id = self.read_uev()
        seq_parameter_set_id = self.read_uev()
        entropy_coding_mode_flag = self.read_bit(1)
        NAL.pic_order_present_flag = self.read_bit(1)
        num_slice_groups_minus1 = self.read_uev()
        if num_slice_groups_minus1 > 0 :
            slice_group_map_type = self.read_uev()
            if slice_group_map_type == 0 :
                for iGroup in range(0, num_slice_groups_minus1 + 1):
                    self.read_uev() #run_length_minus1[ iGroup ] 
            elif slice_group_map_type == 2 :
                for i in range(num_slice_groups_minus1):
                    self.read_uev() #top_left[ iGroup ] 
                    self.read_uev() #bottom_right[ iGroup ]
            elif slice_group_map_type in [3,4,5]:
                slice_group_change_direction_flag = self.read_bit(1)
                slice_group_change_rate_minus1 = self.read_uev()
            elif slice_group_map_type == 6:
                pic_size_in_map_units_minus1 = self.read_uev()
                rangeMinus1 = pic_size_in_map_units_minus1 + 1
                for i in range(rangeMinus1) :
                    self.read_bit(math.ceil(math.log2(num_slice_groups_minus1 + 1)))
        self.num_ref_idx_l0_active_minus1 = self.read_uev()
        num_ref_idx_l1_active_minus1 = self.read_uev()
        NAL.weighted_pred_flag = self.read_bit(1)
        NAL.weighted_bipred_idc = self.read_bit(2)
        pic_init_qp_minus26 = self.read_sev()
        pic_init_qs_minus26 = self.read_sev()
        chroma_qp_index_offset = self.read_sev()
        deblocking_filter_control_present_flag = self.read_bit(1)
        constrained_intra_pred_flag = self.read_bit(1)
        NAL.redundant_pic_cnt_present_flag = self.read_bit(1)

    def ref_pic_list_reordering(self):
        if NAL.SLICE_TYPE(self.slice_type) not in (NAL.SLICE_TYPE_I , NAL.SLICE_TYPE_SI) :
            ref_pic_list_reordering_flag_l0 = self.read_bit(1)
            if ref_pic_list_reordering_flag_l0 == 1:
                while(True):
                    reordering_of_pic_nums_idc = self.read_uev()
                    if reordering_of_pic_nums_idc == 0 or reordering_of_pic_nums_idc == 1:
                        abs_diff_pic_num_minus1 = self.read_uev()
                    elif reordering_of_pic_nums_idc == 2:
                        long_term_pic_num = self.read_uev()
                    elif reordering_of_pic_nums_idc == 3:
                        break
        if NAL.SLICE_TYPE(self.slice_type) == NAL.SLICE_TYPE_B:
            ref_pic_list_reordering_flag_l1 = self.read_bit(1)
            if ref_pic_list_reordering_flag_l1 == 1:
                while(True):
                    reordering_of_pic_nums_idc = self.read_uev()
                    if reordering_of_pic_nums_idc == 0 or reordering_of_pic_nums_idc == 1:
                        abs_diff_pic_num_minus1 = self.read_uev()
                    elif reordering_of_pic_nums_idc == 2:
                        long_term_pic_num = self.read_uev()
                    elif reordering_of_pic_nums_idc == 3:
                        break

    def pred_weight_table(self):
        luma_log2_weight_denom = self.read_uev()
        if self.chroma_format_idc != 0:
            chroma_log2_weight_denom = self.read_uev()
        num_ref_idx_l0_active_minus1_xrange = self.num_ref_idx_l0_active_minus1 + 1
        for i in range(num_ref_idx_l0_active_minus1_xrange):
            luma_weight_l0_flag = self.read_bit(1)
            if luma_weight_l0_flag == 1:
                # luma_weight_l0 = 
                self.read_sev()
                # luma_offset_l0
                self.read_sev()
            if self.chroma_format_idc != 0:
                chroma_weight_l0_flag = self.read_bit(1)
                if chroma_weight_l0_flag == 1:
                    self.read_sev()
                    self.read_sev()
                    self.read_sev()
                    self.read_sev()
                    # chroma_weight_l0
                    # chroma_offset_l0
        if NAL.SLICE_TYPE(self.slice_type) == NAL.SLICE_TYPE_B:
            num_ref_idx_l1_active_minus1_xrange = self.num_ref_idx_l1_active_minus1 + 1
            for i in range(num_ref_idx_l1_active_minus1_xrange):
                luma_weight_l1_flag = self.read_bit(1)
                if luma_weight_l1_flag == 1:
                    # luma_weight_l1
                    # luma_offset_l1
                    self.read_sev()
                    self.read_sev()
                if NAL.chroma_format_idc != 0:
                    chroma_weight_l1_flag = self.read_bit(1)
                    if chroma_weight_l1_flag == 1:
                        # chroma_weight_l1[ i ][ j ] 2 se(v)
                        # chroma_offset_l1[ i ][ j ] 
                        self.read_sev()
                        self.read_sev()
                        self.read_sev()
                        self.read_sev()

    def dec_ref_pic_marking():


    def slice_header(self):
        first_mb_in_slice = self.read_uev()
        self.slice_type = self.read_uev() # 7.4.2.4
        pic_parameter_set_id= self.read_uev()
        frame_num = self.read_bit(NAL.log2_max_frame_num_minus4 + 4)
        if NAL.frame_mbs_only_flag == 0 :
            field_pic_flag = self.read_bit(1)
            if field_pic_flag:
                bottom_field_flag = self.read_bit(1)
        if self.nal_unit_type == 5: 
            idr_pic_id = self.read_uev()
        if NAL.pic_order_cnt_type == 0:
            pic_order_cnt_lsb = self.read_bit(NAL.log2_max_pic_order_cnt_lsb_minus4 + 4)
            if NAL.pic_order_present_flag == 1 and field_pic_flag != 1:
                delta_pic_order_cnt_bottom = self.read_sev()
        if NAL.pic_order_cnt_type == 1 and NAL.delta_pic_order_always_zero_flag != 1:
            # delta_pic_order_cnt[0] = 
            self.read_sev()
            if NAL.pic_order_present_flag == 1 and field_pic_flag != 1 :
                # delta_pic_order_cnt[1] =
                self.read_sev()
        if NAL.redundant_pic_cnt_present_flag :
            redundant_pic_cnt = self.read_uev()
        if NAL.SLICE_TYPE(self.slice_type) == NAL.SLICE_TYPE_B:
            direct_spatial_mv_pred_flag = self.read_bit(1)
        if NAL.SLICE_TYPE(self.slice_type) in (NAL.SLICE_TYPE_P, NAL.SLICE_TYPE_SP, NAL.SLICE_TYPE_B):
            num_ref_idx_active_override_flag = self.read_bit(1)
            if num_ref_idx_active_override_flag == 1:
                num_ref_idx_l0_active_minus1 = self.read_uev()
                if NAL.SLICE_TYPE(self.slice_type) == NAL.SLICE_TYPE_B:
                    self.num_ref_idx_l1_active_minus1 = self.read_uev()
        self.ref_pic_list_reordering()
        if ( NAL.weighted_pred_flag == 1 and NAL.SLICE_TYPE(self.slice_type) in (NAL.SLICE_TYPE_P, NAL.SLICE_TYPE_SP) ) or ( NAL.weighted_bipred_idc == 1 and NAL.SLICE_TYPE(self.slice_type) == NAL.SLICE_TYPE_B ):
            self.pred_weight_table()
        if self.nal_ref_idc != 0 :
            raise("未来实现001")
            self.dec_ref_pic_marking()


    def slice_layer_without_partitioning_rbsp(self):
        self.slice_header()



class H264: 

    # list: List[NAL] = []

    def setNal(self, hex):
        NAL(hex)
    def __init__(self,filename):
        with open(filename, "rb") as f:
            self.hex = bytearray(f.read())
        hexCount = len(self.hex)
        readCount = 0
        sliceStart = 0  
        while hexCount > readCount:
            if self.hex[readCount] != 0 or self.hex[readCount+1] != 0:
                readCount += 1
                continue
            startCodeLen = 0
            if self.hex[readCount+2] == 0:
                if self.hex[readCount+3] == 1: # 0x00000001 分割。
                    startCodeLen = 4
            elif self.hex[readCount+2] == 1: # 0x000001 分割。
                startCodeLen = 3
            elif self.hex[readCount+2] == 3: # 0x000003透明传输字段 emulation_prevention_three_byte 
                del self.hex[readCount+2] # //处理透明传输
                hexCount -= 1
            if startCodeLen == 0:
                readCount += 1
            else:
                if readCount > 0:
                    self.setNal(self.hex[sliceStart:readCount])
                readCount += startCodeLen
                sliceStart = readCount
        self.setNal(self.hex[sliceStart:readCount])# 最后一个结尾

if __name__ == "__main__":
    H264("runtime/output.h264")
