import numpy as np
import math
import cv2

def to_binary_list(n):
    """Convert integer into a list of bits"""
    return [n] if (n <= 1) else to_binary_list(n >> 1) + [n & 1]

def from_binary_list(bits):
    """Convert list of bits into an integer"""
    result = 0
    for bit in bits:
        result = (result << 1) | bit
    return result

def pad_bits(bits, n):
    """Prefix list of bits with enough zeros to reach n digits"""
    assert(n >= len(bits))
    return ([0] * (n - len(bits)) + bits)

class OutputBitStream(object): 
    def __init__(self, file_name): 
        self.file_name = file_name
        self.file = open(self.file_name, 'wb') 
        self.bytes_written = 0
        self.buffer = []

    def write_bit(self, value):
        self.write_bits([value])

    def write_bits(self, values):
        self.buffer += values
        while len(self.buffer) >= 8:
            self._save_byte()        

    def flush(self):
        if len(self.buffer) > 0: # Add trailing zeros to complete a byte and write it
            self.buffer += [0] * (8 - len(self.buffer))
            self._save_byte()
        assert(len(self.buffer) == 0)

    def _save_byte(self):
        bits = self.buffer[:8]
        self.buffer[:] = self.buffer[8:]

        byte_value = from_binary_list(bits)
        self.file.write(bytes([byte_value]))
        self.bytes_written += 1

    def close(self): 
        self.flush()
        self.file.close()


class InputBitStream(object): 
    def __init__(self, file_name): 
        self.file_name = file_name
        self.file = open(self.file_name, 'rb') 
        self.bytes_read = 0
        self.buffer = []

    def read_bit(self):
        return self.read_bits(1)[0]

    def read_bits(self, count):
        while len(self.buffer) < count:
            self._load_byte()
        result = self.buffer[:count]
        self.buffer[:] = self.buffer[count:]
        return result

    def flush(self):
        assert(not any(self.buffer))
        self.buffer[:] = []

    def _load_byte(self):
        value = ord(self.file.read(1))
        self.buffer += pad_bits(to_binary_list(value), 8)
        self.bytes_read += 1

    def close(self): 
        self.file.close()

def getTransformValue(i, j):
    if i == 0:
        return 1/math.sqrt(8)
    else:
        return (1/2)*math.cos(((2*j+1)*i*math.pi)/16)

def generateTransformMatrix():
    M = np.zeros((8, 8))

    for i in range(8):
        for j in range(8):
            M[i][j] = getTransformValue(i, j)

    return M

def applyDCT(m, mt, block):
    return np.matmul(np.matmul(m, block), mt)

def inverseDCT(qm, m, mt, block):
    for i in range(8):
        for j in range(8):
            block[i, j] = np.round(block[i, j]*qm[i][j])

    return np.matmul(np.matmul(mt, block), m)



def main():
    filename = 'lena512.bmp'
    out_filename = 'teste.bmp'

    bytes_array = np.fromfile(filename, dtype = "uint8")
    bits = np.unpackbits(bytes_array)
    header = bits[:54*8]
    header = list(header)

    img = cv2.imread(filename, 0)

    height, width = img.shape[:2]

    quant_matrix = [[16, 11, 10, 16, 24, 40, 51, 61],
              [12, 12, 14, 19, 26, 58, 60, 55],
              [14, 13, 16, 24, 40, 57, 69, 56],
              [14, 17, 22, 29, 51, 87, 80, 62],
              [18, 22, 37, 56, 68, 109, 103, 77],
              [24, 35, 55, 64, 81, 104, 113, 92],
              [49, 64, 78, 87, 103, 121, 120, 101],
              [72, 92, 95, 98, 112, 100, 103, 99]]

    m = generateTransformMatrix()
    
    mt = np.transpose(m)
    
    temp = np.zeros((width, height))
    nimg = np.zeros((width, height))

    #FAZ O DCT
    for i in range(0, height, 8):
        for j in range(0, width, 8):

            block = img[i:i+8, j:j+8]
            dct = applyDCT(m, mt, block)
            block = np.around(np.divide(dct, quant_matrix))


            temp[i:i+8, j:j+8] = block

    #REVERTE O DCT
    for i in range(0, height, 8):
        for j in range(0, width, 8):
            block = temp[i:i+8, j:j+8]


            idct = inverseDCT(quant_matrix, m, mt, block)

            block = np.uint8(np.around(idct))

            nimg[i:i+8, j:j+8] = block

    print("\nImagem Original")
    print(img)
    print("\nImagem apos o DCT")
    print(temp)
    print("\nImagem ao reverter o DCT")
    print(nimg)



if __name__ == '__main__':
    main()