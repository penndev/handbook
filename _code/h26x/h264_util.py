
class Matrix:
    '''
        x y 二维矩阵类型
    '''
    def __init__(self, default=0):
        self.data = {}
        self.default = default
    def __getitem__(self, key):
        x, y = key
        return self.data.get((x, y), self.default)  # 默认值为 0

    def __setitem__(self, key, value):
        x, y = key
        self.data[(x, y)] = value

def InverseRasterScan(a, b, c, d, e):
    if e == 0:
        return (a % (d // b)) * b
    elif e == 1:
        return (a // (d // b)) * c
    else:
        raise('InverseRasterScan error')

def Clip3(minVal, maxVal, value):
    return min(max(value, minVal), maxVal)

Min = min

Max = max