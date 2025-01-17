
def InverseRasterScan(a, b, c, d, e):
    if e == 0:
        return (a % (d // b)) * b
    elif e == 1:
        return (a // (d // b)) * c
    else:
        raise('InverseRasterScan error')

def Clip3(minVal, maxVal, value):
    return min(max(value, minVal), maxVal)
