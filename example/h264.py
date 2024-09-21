
class H264: 
    list = []
    def setFile(self,filename):
        '根据flv文件进行tag分析与提取'
        with open(filename, 'rb') as f:
            self.hex = bytearray(f.read())
        hexCount = len(self.hex)
        readCount = 0
        nal = bytearray()
        while hexCount > readCount:
            if self.hex[readCount] == 0 and self.hex[readCount+1] == 0 :
                if self.hex[readCount+2] == 1 or (self.hex[readCount+2] == 0 and self.hex[readCount+3] == 1): 
                    self.list.append(nal)
                    nal = bytearray()
            nal.append(self.hex[readCount])
            readCount += 1
        self.list = self.list[1:]

if __name__ == "__main__":
    v = H264()
    v.setFile("./vfile/output.h264")
    print(v.list)