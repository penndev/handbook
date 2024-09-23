
class H264: 
    list = []
    def setFile(self,filename):
        with open(filename, 'rb') as f:
            self.hex = bytearray(f.read())
        hexCount = len(self.hex)
        readCount = 0
        sliceStart = 0  
        while hexCount > readCount:
            if self.hex[readCount] != 0 or self.hex[readCount+1] != 0:
                readCount += 1
                continue
            
            startCodeLen = 0
            if self.hex[readCount+2] == 0 :
                if self.hex[readCount+3] == 1 :
                    startCodeLen = 4
            elif self.hex[readCount+2] == 1 :
                startCodeLen = 3

            if startCodeLen == 0:
                readCount += 1
            else:
                if readCount > 0:
                    self.list.append(self.hex[sliceStart:readCount])
                readCount += startCodeLen
                sliceStart = readCount
        # 最后一个结尾
        self.list.append(self.hex[sliceStart:readCount])
        
            

if __name__ == "__main__":
    v = H264()
    v.setFile("./vfile/output.h264")
    with open("./vfile/output.bin", "wb") as file:
        for element in v.list:
            file.write(element)