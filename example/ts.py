'''
>   Mpeg2-TS 初次接触是因为hls默认生成的视频封装的格式
给我的感觉是封装复杂 ts层 pes层 es层 而且其188*0xff的固定填充造成冗余
格式较老 用于web封装显得冗杂 但是还是值得学习的视频概念

参考文档：
    > ISO/IEC 13818-1 2.6.9 标准
    - `https://www.itu.int/rec/T-REC-H.222.0-199507-S` [国际电联标准文档]
    - `https://en.wikipedia.org/wiki/MPEG_transport_stream` [ts的数据结构]
    - `https://dvd.sourceforge.net/dvdinfo/pes-hdr.html` [pes的数据结构]
    
    > 可参考不详细
    - `https://tsduck.io/download/docs/mpegts-introduction.pdf`
    - `https://www.etsi.org/deliver/etsi_i_ets/300400_300499/300468/02_30_113/ets_300468e02v.pdf`
    - `https://www.etsi.org/deliver/etsi_en/300400_300499/300468/01.13.01_40/en_300468v011301o.pdf
'''

# 计算psi/si的crc32方法
def calculate_crc32(data):
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte << 24
        for _ in range(8):
            if crc & 0x80000000:
                crc = (crc << 1) ^ 0x04C11DB7
            else:
                crc <<= 1
    return crc & 0xFFFFFFFF

class TsServiceDescriptionTable:
    def __init__(self, data: bytearray | None = None) -> None:
        if data is None:
            return 
        self.table_id = data[0]
        self.section_syntax_indicator = data[1] >> 7
        # self.reserved_future_use = (data[1] >> 6) & 1
        # self.reserved = (data[1] >> 4) & 3
        self.section_length = (data[1] & 0x0f) << 8
        self.section_length += data[2] 
        self.transport_stream_id = (data[3] << 8) + data[4]
        # self.reserved = data[5] >> 6
        self.version_number = (data[5] >> 1) & 0x1f
        self.current_next_indicator = data[5] & 1
        self.section_number = data[6]
        self.last_section_number = data[7]
        self.original_network_id = (data[8] << 8) + data[9]
        # self.reserved_future_use = data[10]
        # 计算剩余字节
        end = self.section_length + 3
        section = data[11:end-4]

        self.section_list = []
        i = 0
        while i < len(section):
            section_map = {}
            section_map["service_id"] = int.from_bytes(section[i:i+2], "big")
            i += 2
            section_map["EIT_schedule_flag"] = (section[i] >> 1) & 1
            section_map["EIT_present_following_flag"] = section[i]  & 1
            i += 1
            section_map["running_status"] = section[i] >> 5
            section_map["free_CA_mode"] = (section[i] >> 4) & 1
            section_map["descriptors_loop_length"] = (section[i] & 0x0f) << 8
            i += 1
            section_map["descriptors_loop_length"] += section[i]
            i += 1
            descriptors = section[i:i+section_map["descriptors_loop_length"]]
            i += section_map["descriptors_loop_length"]
            section_map["descriptors"] = []
            ii = 0
            while ii < len(descriptors):
                descriptors_map = {}
                descriptors_map["descriptor_tag"] = descriptors[ii]
                ii += 1
                descriptors_map["descriptor_length"] = descriptors[ii]
                ii += 1
                descriptors_map["service_type"] = descriptors[ii]
                ii += 1
                descriptors_map["service_provider_name_length"] = descriptors[ii]
                ii += 1
                descriptors_map["service_provider_name"] = descriptors[ii:ii+descriptors_map["service_provider_name_length"]]
                ii += descriptors_map["service_provider_name_length"]
                descriptors_map["service_name_length"] = descriptors[ii]
                ii += 1
                descriptors_map["service_name"] = descriptors[ii:ii+descriptors_map["service_name_length"]]
                ii += descriptors_map["service_name_length"]
                section_map["descriptors"].append(descriptors_map)
            self.section_list.append(section_map)
        self.crc_32 = int.from_bytes(data[end-4:end],"big")


    def tobyte(self):
        data = bytearray([0]*11)
        data[0] = self.table_id
        data[1] = self.section_syntax_indicator << 7
        data[1] |= 0x40
        data[1] |= 3 << 4
        data[1] |= ( self.section_length << 8 ) & 0x0f
        data[2] = self.section_length & 0xff
        data[3] = self.transport_stream_id >> 8
        data[4] = self.transport_stream_id & 0xff
        data[5] = 0xc0
        data[5] |= self.version_number << 1
        data[5] |= self.current_next_indicator 
        data[6] = self.section_number
        data[7] = self.last_section_number
        data[8] = self.original_network_id >> 8
        data[9] = self.original_network_id & 0xff
        data[10] = 0xff
        # 生成 section
        for item_section in self.section_list:
            item_section_byte = bytearray([0] * 5)
            item_section_byte[0] = (item_section["service_id"] >> 8) & 0xff
            item_section_byte[1] = item_section["service_id"] & 0xff
            item_section_byte[2] = 0xfc
            item_section_byte[2] |= item_section["EIT_schedule_flag"] << 1
            item_section_byte[2] |= item_section["EIT_present_following_flag"] 
            item_section_byte[3] = item_section["running_status"] << 5
            item_section_byte[3] |= item_section["free_CA_mode"] << 4
            item_section_byte[3] |= item_section["descriptors_loop_length"] >> 8
            item_section_byte[4] = item_section["descriptors_loop_length"] & 0xff
            data += item_section_byte
            for descriptors in item_section["descriptors"]:
                descriptors_byte = bytearray([0] * 4)
                descriptors_byte[0] = descriptors["descriptor_tag"]
                descriptors_byte[1] = descriptors["descriptor_length"]
                descriptors_byte[2] = descriptors["service_type"]
                descriptors_byte[3] = descriptors["service_provider_name_length"]
                descriptors_byte += descriptors["service_provider_name"]
                descriptors_byte += bytearray([descriptors["service_name_length"]])
                descriptors_byte += descriptors["service_name"]
                # 生成数据
                data += descriptors_byte
        crc_32_byte = self.crc_32.to_bytes(4, "big")
        data += crc_32_byte
        return data
        # 

    def genSDT(self):
        self.table_id = 66
        self.section_syntax_indicator = 1
        self.section_length = 37
        self.transport_stream_id = 1
        self.version_number = 0
        self.current_next_indicator = 1
        self.section_number = 0
        self.last_section_number = 0
        self.original_network_id = 65281
        self.section_list = [
            {
                'service_id': 1, 
                'EIT_schedule_flag': 0, 
                'EIT_present_following_flag': 0, 
                'running_status': 4, 
                'free_CA_mode': 0, 
                'descriptors_loop_length': 20, 
                'descriptors': [
                    {
                        'descriptor_tag': 72, 
                        'descriptor_length': 18, 
                        'service_type': 1, 
                        'service_provider_name_length': 6, 
                        'service_provider_name': bytearray(b'FFmpeg'), 
                        'service_name_length': 9, 
                        'service_name': bytearray(b'Service01')
                    }
                ]
            }
        ]
        self.crc_32 = 2004632522
        sdt_byte = bytearray([0x47, 0x40, 0x11, 0x10, 0x00]) + self.tobyte()
        data = bytearray([0xff]*188)
        data[0:len(sdt_byte)] = sdt_byte
        return data

class TsProgramAssociationTable:
    def __init__(self, data: bytearray | None = None) -> None:
        if data is None:
            return 
        self.table_id = data[0]
        self.section_syntax_indicator = data[1] >> 7
        self.section_length = (data[1] & 0x0f) << 8
        self.section_length += data[2] 
        self.transport_stream_id = (data[3] << 8) + data[4]
        self.version_number = (data[5] >> 1) & 0x1f
        self.current_next_indicator = data[5] & 1
        self.section_number = data[6]
        self.last_section_number = data[7]
        self.program_number = (data[8] << 8) + data[9]
        self.program_map_PID = ((data[10] & 0x1f) << 8) + data[11]

        end = self.section_length + 3
        self.crc_32 = int.from_bytes(data[end-4:end],"big")

    def tobyte(self):
        data = bytearray([0]*12)
        data[0] = self.table_id
        data[1] = 0xb0 | (( self.section_length >> 8 ) & 0x0f)
        data[2] = self.section_length & 0xff
        data[3] = self.transport_stream_id >> 8
        data[4] = self.transport_stream_id & 0xff
        data[5] = 0xc0 | (self.version_number << 1)
        data[5] |= self.current_next_indicator 
        data[6] = self.section_number
        data[7] = self.last_section_number
        data[8] = self.program_number >> 8
        data[9] = self.program_number & 0xff
        data[10] = (self.program_map_PID >> 8) | 0xe0
        data[11] = self.program_map_PID & 0xff
        crc_32_byte = self.crc_32.to_bytes(4, "big")
        data += crc_32_byte
        return data

    def genPAT(self):
        self.table_id = 0
        self.section_syntax_indicator = 1
        self.section_length = 13
        self.transport_stream_id = 1
        self.version_number = 0
        self.current_next_indicator = 1
        self.section_number = 0
        self.last_section_number = 0
        self.program_number = 1
        self.program_map_PID = 4096
        self.crc_32 = 716244146
        pat_byte = self.tobyte()
        data = bytearray([0xff] * 188)
        data[:5] = [0x47, 0x40, 0x00, 0x10,  0x00]
        data[5:5+len(pat_byte)] = pat_byte
        return data

class TsProgramMapTable:
    def __init__(self, data: bytearray | None = None) -> None:
        if data is None:
            return 
        self.table_id = data[0]
        self.section_syntax_indicator = data[1] >> 7
        self.section_length = (data[1] & 0x0f) << 8
        self.section_length += data[2] 
        self.transport_stream_id = (data[3] << 8) + data[4]
        self.version_number = (data[5] >> 1) & 0x1f
        self.current_next_indicator = data[5] & 1
        self.section_number = data[6]
        self.last_section_number = data[7]
        self.PCR_PID = ((data[8] & 0x1f) << 8) | data[9]
        self.program_info_length = (data[10] & 0x0f << 8) | data[11]

        end = self.section_length + 3
        program = data[12:end-4]

        self.program_list = []
        i = 0
        while i < len(program):
            program_map = {}
            program_map["stream_type"] = program[i]
            i += 1
            program_map["elementary_PID"] = ((program[i] & 0x1f) << 8) | program[i+1]
            i += 2
            program_map["ES_info_length"] = (program[i] & 0x0f << 8) | program[i+1]
            i += 2 
            i += program_map["ES_info_length"]
            self.program_list.append(program_map)
        self.crc_32 = int.from_bytes(data[end-4:end],"big")

    def tobyte(self):
        data = bytearray([0]*12)
        data[0] = self.table_id
        data[1] = 0xb0
        data[1] |= ( self.section_length << 8 ) & 0x0f
        data[2] = self.section_length & 0xff
        data[3] = self.transport_stream_id >> 8
        data[4] = self.transport_stream_id & 0xff
        data[5] = 0xc0
        data[5] |= self.version_number << 1
        data[5] |= self.current_next_indicator 
        data[6] = self.section_number
        data[7] = self.last_section_number
        data[8] = (self.PCR_PID >> 8) | 0xe0
        data[9] = self.PCR_PID & 0xff
        data[10] = (self.program_info_length >> 8) | 0xf0
        data[11] = self.program_info_length & 0xff

        for program_map in self.program_list:
            program_byte = bytearray([0] * 5)
            program_byte[0] = program_map["stream_type"]
            program_byte[1] = (program_map["elementary_PID"] >> 8) | 0xe0
            program_byte[2] = program_map["elementary_PID"] & 0xff
            program_byte[3] = (program_map["ES_info_length"] >> 8) | 0xf0
            program_byte[4] = program_map["ES_info_length"] & 0xff
            program_byte += bytearray([0]*program_map["ES_info_length"])
            data += program_byte

        crc_32_byte = self.crc_32.to_bytes(4, "big")
        data += crc_32_byte
        return data        

    def genPMT(self):
        self.table_id = 2
        self.section_syntax_indicator = 1
        self.section_length = 23
        self.transport_stream_id = 1
        self.version_number = 0
        self.current_next_indicator = 1
        self.section_number = 0
        self.last_section_number = 0
        self.PCR_PID = 256
        self.program_info_length = 0
        self.program_list = [
            {'stream_type': 27, 'elementary_PID': 256, 'ES_info_length': 0}, 
            {'stream_type': 15, 'elementary_PID': 257, 'ES_info_length': 0}
        ]
        self.crc_32 = 793033115
        pmt_byte = bytearray([0x47, 0x50, 0x00, 0x10, 0x00]) + self.tobyte()
        data = bytearray([0xff]*188)
        data[:len(pmt_byte)] = pmt_byte
        return data

class PesPacket:
    @staticmethod
    def get_pts_dts(pts: bytearray) -> int:
        value = ((pts[0] & 0x0E) << 29) | \
            ((pts[1] & 0xFF) << 22) | \
            ((pts[2] & 0xFE) << 14) | \
            ((pts[3] & 0xFF) << 7) | \
            ((pts[4] & 0xFE) >> 1)
        return value

    @staticmethod
    def set_pts_dts(value: int, mask: int) -> bytearray:
        pts = bytearray(5)
        pts[0] = (value >> 29) & 0x0E | 1 | mask
        pts[1] = (value >> 22) & 0xFF
        pts[2] = (value >> 14) & 0xFE | 1
        pts[3] = (value >> 7) & 0xFF
        pts[4] = (value << 1) & 0xFE | 1
        return pts

    def __init__(self, pes: bytearray) -> None:
        self.stream_id = None
        self.PES_packet_length = None
        self.PES_scrambling_control = None
        self.PES_priority = None
        self.data_alignment_indicator = None
        self.copyright = None
        self.original_or_copy = None
        self.PTS_DTS_flags = None
        self.ESCR_flag = None
        self.ES_rate_flag = None
        self.DSM_trick_mode_flag = None
        self.additional_copy_info_flag = None
        self.PES_CRC_flag = None
        self.PES_extension_flag = None
        self.PES_header_data_length = None
        self.PTS = None
        self.DTS = None

        self.payload = None

        ##
        if pes[0:3] != bytearray([0, 0, 1]):
            raise Exception("错误的pes开头")
        self.stream_id = pes[3]
        self.PES_packet_length = (pes[4] << 8) | pes[5]
        self.PES_scrambling_control = (pes[6] & 30) >> 4
        self.PES_priority = (pes[6] & 4) >> 3
        self.data_alignment_indicator = (pes[6] & 3) >> 2
        self.copyright = (pes[6] & 2) >> 1
        self.original_or_copy = pes[6] & 1
        self.PTS_DTS_flags = (pes[7] & 0xc0) >> 6
        self.ESCR_flag = (pes[7] >> 5) & 1
        self.ES_rate_flag = (pes[7] >> 4) & 1
        self.DSM_trick_mode_flag = (pes[7] >> 3) & 1
        self.additional_copy_info_flag = (pes[7] >> 2) & 1
        self.PES_CRC_flag = (pes[7] >> 1) & 1
        self.PES_extension_flag = pes[7] & 1
        self.PES_header_data_length = pes[8]
        if self.PTS_DTS_flags == 1:
            raise Exception("提取错误的值 PTS_DTS_flags")
        elif self.PTS_DTS_flags == 2:  # 0b10
            self.PTS = PesPacket.get_pts_dts(pes[9:14])
        elif self.PTS_DTS_flags == 3:  # 0b11
            self.PTS = PesPacket.get_pts_dts(pes[9:14])
            self.DTS = PesPacket.get_pts_dts(pes[14:19])
        self.payload = pes[8+self.PES_header_data_length:]

    def tobyte(self):
        pes = bytearray(9)
        pes[0:3] = [0, 0, 1]
        pes[3] = self.stream_id
        pes[4] = self.PES_packet_length >> 8
        pes[5] = self.PES_packet_length & 0xFF
        pes[6] = 0x80
        pes[6] |= self.PES_scrambling_control << 4
        pes[6] |= self.PES_priority << 3
        pes[6] |= self.data_alignment_indicator << 2
        pes[6] |= self.copyright << 1
        pes[6] |= self.original_or_copy
        pes[7] = self.PTS_DTS_flags << 6
        pes[7] |= self.ESCR_flag << 5
        pes[7] |= self.ES_rate_flag << 4
        pes[7] |= self.DSM_trick_mode_flag << 3
        pes[7] |= self.additional_copy_info_flag << 2
        pes[7] |= self.PES_CRC_flag << 1
        pes[7] |= self.PES_extension_flag
        pes[8] = self.PES_header_data_length
        if self.PTS_DTS_flags == 2:
            pes += PesPacket.set_pts_dts(self.PTS, 0x20)
        elif self.PTS_DTS_flags == 3:
            pes += PesPacket.set_pts_dts(self.PTS, 0x30)
            pes += PesPacket.set_pts_dts(self.DTS, 0x10)
        pes[8+self.PES_header_data_length:] = self.payload
        return pes

class TsPacket:
    def __init__(self, data: bytearray | None = None):
        '''
            每个ts packet大小为188字节
            将188字节进行拆分编码
        '''
        # ts packet header
        self.sync = 0x47  # 固定标识头 0x47 71
        self.transport_error_indicator = 0
        self.payload_unit_start_indicator = 0
        self.transport_priority = 0
        self.pid = 0
        self.transport_scrambling_control = 0
        self.adaptation_field_control = 0
        self.continuity_counter = 0
        # ts packet adaptation
        self.adaptation_field_length = 0
        self.discontinuity_indicator = 0
        self.random_access_indicator = 0
        self.elementary_stream_priority_indicator = 0
        self.PCR_flag = 0
        self.OPCR_flag = 0
        self.splicing_point_flag = 0
        self.transport_private_data_flag = 0
        self.adaptation_field_extension_flag = 0
        self.pcr_base = 0      # - if self.PCR_flag == 1
        self.pcr_extension = 0 # - (pcr_base * 300 + pcr_extension) / 27hz = pcr
        # ts packet payload
        self.payload = None  # - pes data
        # -------------------------------------------------------------------------------
        # -------------------------------------------------------------------------------
        # -------------------------------------------------------------------------------
        if data is None:
            return
        if len(data) != 188:
            raise Exception("数据长度不足188")
        if data[0] != 0x47:
            raise Exception("同步字节错误，应为0x47")
        #
        self.sync = data[0]
        self.transport_error_indicator = data[1] >> 7
        self.payload_unit_start_indicator = data[1] >> 6 & 1
        self.transport_priority = data[1] >> 5 & 1
        self.pid = int.from_bytes([data[1] & 0x1f, data[2]], "big")
        self.transport_scrambling_control = data[3] >> 6
        self.adaptation_field_control = data[3] >> 4 & 3
        self.continuity_counter = data[3] & 0x0f
        if self.adaptation_field_control == 3 or self.adaptation_field_control == 2:
            self.adaptation_field_length = data[4]
            self.discontinuity_indicator = data[5] >> 7
            self.random_access_indicator = (data[5] >> 6) & 1
            self.elementary_stream_priority_indicator = (data[5] >> 5) & 1
            self.PCR_flag = (data[5] >> 4) & 1
            self.OPCR_flag = (data[5] >> 3) & 1
            self.splicing_point_flag = (data[5] >> 2) & 1
            self.transport_private_data_flag = (data[5] >> 1) & 1
            self.adaptation_field_extension_flag = data[5] & 1
            if self.PCR_flag == 1:
                pcr_data = data[6:12]
                self.pcr_base = 0 | (pcr_data[0] & 0xFF) << 25
                self.pcr_base |= (pcr_data[1] & 0xFF) << 17
                self.pcr_base |= (pcr_data[2] & 0xFF) << 9
                self.pcr_base |= (pcr_data[3] & 0xFF) << 1
                self.pcr_base |= (pcr_data[4] & 0x80) >> 7
                self.pcr_extension = ((pcr_data[4] & 0x01) << 8) | (pcr_data[5] & 0xFF)

            self.payload = data[5+self.adaptation_field_length:]
        elif self.adaptation_field_control == 1:
            self.payload = data[4:]
        else:
            raise Exception("错误的 adaptation_field_control")

    def tobyte(self):
        '''
            封装数据到ts 字节数据
        '''
        data = bytearray([0XFF] * 188)
        data[0] = self.sync
        data[1] = 0
        if self.transport_error_indicator:
            data[1] |= 0x80
        if self.payload_unit_start_indicator:
            data[1] |= 0x40
        if self.transport_priority:
            data[1] |= 0x20
        data[1] |= (self.pid >> 8) & 0x1f
        data[2] = self.pid & 0xff
        data[3] = 0
        data[3] |= (self.transport_scrambling_control & 0xff) << 6
        data[3] |= (self.adaptation_field_control & 0x3f) << 4
        data[3] |= self.continuity_counter & 0x0f
        # 完成head
        if self.adaptation_field_control == 3 or self.adaptation_field_control == 2:
            data[4] = self.adaptation_field_length
            data[5] = 0
            data[5] |= self.discontinuity_indicator << 7
            data[5] |= self.random_access_indicator << 6
            data[5] |= self.elementary_stream_priority_indicator << 5
            data[5] |= self.PCR_flag << 4
            data[5] |= self.OPCR_flag << 3
            data[5] |= self.splicing_point_flag << 2
            data[5] |= self.transport_private_data_flag << 1
            data[5] |= self.adaptation_field_extension_flag

            if self.PCR_flag == 1:
                pcr_data = bytearray(6)
                pcr_data[0] = (self.pcr_base >> 25) & 0xFF
                pcr_data[1] = (self.pcr_base >> 17) & 0xFF
                pcr_data[2] = (self.pcr_base >> 9) & 0xFF
                pcr_data[3] = (self.pcr_base >> 1) & 0xFF
                pcr_data[4] = self.pcr_base << 7 & 0xFF | 0x7e 
                pcr_data[4] |= (self.pcr_extension >> 8) & 0x01
                pcr_data[5] = self.pcr_extension & 0xFF
                data[6:12] = pcr_data
            data[5+self.adaptation_field_length:] = self.payload
        elif self.adaptation_field_control == 1:
            data[4:] = self.payload
        else:
            raise Exception("错误的 adaptation_field_control")
        if len(data) != 188:
            raise Exception("错误的 数据长度")
        return data

class Ts:
    VIDEO_COUNT=0
    AUDIO_COUNT=0

    VIDEO_PID = 0x100
    AUDIO_PID = 0x101

    FILE_IN = None
    FILE_OUT = None

    # adaptation_field_control = 11 | 176 byte
    def set_adaptation_11(self, pcr_base, pcr_ext, pid, pes):
        pk = TsPacket()
        pk.payload_unit_start_indicator = 1
        pk.pid = pid
        pk.transport_scrambling_control = 0
        pk.adaptation_field_control = 3
        if pid == self.VIDEO_PID:
            pk.continuity_counter = self.VIDEO_COUNT % 16
            self.VIDEO_COUNT += 1
        elif pid == self.AUDIO_PID:
            pk.continuity_counter = self.AUDIO_COUNT % 16
            self.AUDIO_COUNT += 1
        else:
            raise Exception("错误的pid", pid)
        # 
        pk.adaptation_field_length = 183 - len(pes)
        # pk.random_access_indicator = 1
        pk.PCR_flag = 1
        pk.pcr_base = pcr_base
        pk.pcr_extension = pcr_ext
        # head 4 + adaption(1) +  number(adaption) = 12
        pk.payload = pes  # - pes data
        self.FILE_OUT.write(pk.tobyte())

    # adaptation_field_control = 11 | 182 byte
    def set_adaptation_11_pcr0(self, pid, pes):
        pk = TsPacket()
        pk.payload_unit_start_indicator = 1
        pk.pid = pid
        pk.transport_scrambling_control = 0
        pk.adaptation_field_control = 3
        if pid == self.VIDEO_PID:
            pk.continuity_counter = self.VIDEO_COUNT % 16
            self.VIDEO_COUNT += 1
        elif pid == self.AUDIO_PID:
            pk.continuity_counter = self.AUDIO_COUNT % 16
            self.AUDIO_COUNT += 1
        else:
            raise Exception("错误的pid", pid)
        # 
        pk.adaptation_field_length = 183 - len(pes)
        # pk.random_access_indicator = 1
        pk.PCR_flag = 0
        pk.payload = pes  # - pes data
        self.FILE_OUT.write(pk.tobyte())

    # adaption_field_control = 11 | <184 byte
    def set_adaptation_11_last(self,pid,pes):
        pk = TsPacket()
        pk.pid = pid
        pk.transport_scrambling_control = 0
        pk.adaptation_field_control = 3
        if pid == self.VIDEO_PID:
            pk.continuity_counter = self.VIDEO_COUNT % 16
            self.VIDEO_COUNT += 1
        elif pid == self.AUDIO_PID:
            pk.continuity_counter = self.AUDIO_COUNT % 16
            self.AUDIO_COUNT += 1
        else:
            raise Exception("错误的pid", pid)
        pk.adaptation_field_length = 183 - len(pes)
        pk.payload = pes  # - pes data
        self.FILE_OUT.write(pk.tobyte())

    # adaptation_field_control = 01 | 184 byte
    def set_adaptation_01(self, pid, pes):
        pk = TsPacket()
        pk.pid = pid
        pk.adaptation_field_control = 1
        if pid == self.VIDEO_PID:
            pk.continuity_counter = self.VIDEO_COUNT % 16
            self.VIDEO_COUNT += 1
        elif pid == self.AUDIO_PID:
            pk.continuity_counter = self.AUDIO_COUNT % 16
            self.AUDIO_COUNT += 1
        else:
            raise Exception("错误的pid", pid)
        pk.payload = pes
        self.FILE_OUT.write(pk.tobyte())

    def set_pes(self,pcr_base, pcr_ext, pid, pes):
        # 第一帧
        if pcr_base == 0 and pcr_ext == 0 :
            self.set_adaptation_11_pcr0(pid, pes[:182])
            pes = pes[182:]
        else:
            self.set_adaptation_11(pcr_base, pcr_ext, pid, pes[:176])
            pes = pes[176:]
        # 中间帧
        while len(pes) >= 184:
            self.set_adaptation_01(pid, pes[:184])
            pes = pes[184:]
        # 最后帧
        if len(pes) > 0:
            self.set_adaptation_11_last(pid, pes)

    def __init__(self, in_file:str, out_file:str) -> None:

        self.FILE_IN = open(in_file, "rb") 
        self.FILE_OUT = open(out_file, "wb")

        self.FILE_OUT.write(TsServiceDescriptionTable().genSDT())
        self.FILE_OUT.write(TsProgramAssociationTable().genPAT())
        self.FILE_OUT.write(TsProgramMapTable().genPMT())
        # self.FILE_OUT.write(PMT())

        pes_video = bytearray()
        pcr_base_v = 0
        pcr_ext_v = 0

        pes_audio = bytearray()
        pcr_base_a = 0
        pcr_ext_a = 0
        
        while True:
            # 文件字节流转换为 Ts Pakcet
            i_pk = self.FILE_IN.read(188)
            if not i_pk:
                # 最后一帧 视频
                pes_pack = PesPacket(pes_video)
                self.set_pes(pcr_base_v, pcr_ext_v, 0x100, pes_pack.tobyte())
                # 最后一帧 音频
                pes_pack = PesPacket(pes_audio)
                self.set_pes(pcr_base_a, pcr_ext_a, 0x101, pes_pack.tobyte())
                break
            
            ts_pack = TsPacket(i_pk)

            if ts_pack.pid == 0x100:  # 视频
                if ts_pack.payload_unit_start_indicator == 1:
                    if len(pes_video) > 0 : # 保存实际数据
                        pes_pack = PesPacket(pes_video)
                        self.set_pes(pcr_base_v, pcr_ext_v, ts_pack.pid, pes_pack.tobyte())
                    pes_video = bytearray()
                    pcr_base_v = ts_pack.pcr_base
                    pcr_ext_v = ts_pack.pcr_extension
                pes_video += ts_pack.payload

            elif ts_pack.pid == 0x101:  # 音频
                if ts_pack.payload_unit_start_indicator == 1 :
                    if len(pes_audio) > 0:
                        pes_pack = PesPacket(pes_audio)
                        self.set_pes(pcr_base_a, pcr_ext_a, ts_pack.pid, pes_pack.tobyte())
                    pes_audio = bytearray()
                    pcr_base_a = ts_pack.pcr_base
                    pcr_ext_a = ts_pack.pcr_extension
                pes_audio += ts_pack.payload


def test_ts(filepath: str):
    with open(filepath, "rb") as i_file:
        with open(filepath + ".b", "wb") as w_file:
            while True:
                # 文件字节流转换为 Ts Pakcet
                i_pk = i_file.read(188)
                if not i_pk:
                    break
                ts_pack = TsPacket(i_pk)
                if ts_pack.adaptation_field_control == 3 and ts_pack.pid == 256: 
                    print(ts_pack.pid, ts_pack.payload_unit_start_indicator)
                w_file.write(ts_pack.tobyte())

def test_pes(filepath: str):

    fi = open("fin.pes", "wb")
    fo = open("out.pes", "wb")

    pes_video = bytearray()
    pes_audio = bytearray()
    with open(filepath, "rb") as i_file:
        while True:
            # 文件字节流转换为 Ts Pakcet
            i_pk = i_file.read(188)
            if not i_pk:
                break
            ts_pack = TsPacket(i_pk)

            # Ts Packet 提取 PES
            if ts_pack.pid == 0x100:  # 视频
                if ts_pack.payload_unit_start_indicator == 1 and len(pes_video) > 0:

                    fi.write(pes_video)
                    pes_pack = PesPacket(pes_video)
                    fo.write(pes_pack.tobyte())


                    pes_video = ts_pack.payload  # 必须置空
                else:
                    pes_video += ts_pack.payload
            elif ts_pack.pid == 0x101:  # 音频
                if ts_pack.payload_unit_start_indicator == 1 and len(pes_audio) > 0:

                    fi.write(pes_audio)
                    pes_pack = PesPacket(pes_audio)
                    fo.write(pes_pack.tobyte())


                    pes_audio = ts_pack.payload  # 必须置空
                else:
                    pes_audio += ts_pack.payload

if __name__ == "__main__":
    Ts("i.ts", "o.ts")


