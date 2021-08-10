from numpy.core.defchararray import index
from main import encode_header
import numpy as np
import math
import cv2
from numpy.core.fromnumeric import shape

QUANT_MATRIX = [[16, 11, 10, 16, 24, 40, 51, 61],
              [12, 12, 14, 19, 26, 58, 60, 55],
              [14, 13, 16, 24, 40, 57, 69, 56],
              [14, 17, 22, 29, 51, 87, 80, 62],
              [18, 22, 37, 56, 68, 109, 103, 77],
              [24, 35, 55, 64, 81, 104, 113, 92],
              [49, 64, 78, 87, 103, 121, 120, 101],
              [72, 92, 95, 98, 112, 100, 103, 99]]

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

def zigzag(m):
    count = 1
    direction = -1
    result = []
    currentX = 0
    currentY = 0
    n = shape(m)[0]*2 - 1
    for i in range(n):
        for x in range(count):
            result.append(int(m[currentY, currentX]))
            if x == count -1:
                break
            elif direction == 1:
                currentY -= 1
                currentX += 1
            elif direction == -1:
                currentY += 1
                currentX -= 1
        if i < math.floor(n/2) :
            if direction == 1:
                currentX += 1
                direction = -1
            elif direction == -1:    
                currentY += 1
                direction = 1
            count += 1
        else:
            if direction == 1:
                currentY += 1
                direction = -1
            elif direction == -1:
                currentX += 1
                direction = 1
            count -= 1  
    return result

def reverseZigzag(zz):
    count = 1
    arrayPosition = 0
    direction = -1
    size = int(math.sqrt(len(zz)))
    result = np.zeros((size, size))
    currentX = 0
    currentY = 0
    n = size*2 - 1
    for i in range(n):
        for x in range(count):
            result[currentY, currentX] = float(zz[arrayPosition])
            arrayPosition += 1
            if x == count -1:
                break
            elif direction == 1:
                currentY -= 1
                currentX += 1
            elif direction == -1:
                currentY += 1
                currentX -= 1
        if i < math.floor(n/2) :
            if direction == 1:
                currentX += 1
                direction = -1
            elif direction == -1:    
                currentY += 1
                direction = 1
            count += 1
        else:
            if direction == 1:
                currentY += 1
                direction = -1
            elif direction == -1:
                currentX += 1
                direction = 1
            count -= 1 
    return result

def rLEncode(array):
    lastNonZero = 0
    zerosCount = 0
    result = []
    for i in range(len(array)-1, -1, -1):
        if array[i] != 0:
            lastNonZero = i
            break
        zerosCount += 1
    result.append(lastNonZero+1)
    for i in range(lastNonZero+1):
        result.append(array[i])
    result.append(zerosCount)
    return result

def reverseRLE(array):
    result = []
    zerosCount = array[len(array)-1]
    for i in range(array[0]):
        result.append(array[i+1])
    for i in range(zerosCount):
        result.append(0)
    return result

def convertToByteArray(a):
    result = []
    for i in range(len(a)):
        # result[i] = [to_binary_list(a[i])]
        if a[i] < 0:
            a[i] = a[i]*-1
        result.append(pad_bits(to_binary_list(a[i]), 8))
    return result

def encode_block(block):
    zz = zigzag(block)
    rle = rLEncode(zz)
    return rle

def encode_pixels(img, hw, stream):
    m = generateTransformMatrix()
    mt = np.transpose(m)
    height, width = hw
    for i in range(0, height, 8):
        for j in range(0, width, 8):
            block = img[i:i+8, j:j+8]                       #a 8x8 block
            dct = applyDCT(m, mt, block)                    #applying the dct into the matrix
            block = np.around(np.divide(dct, QUANT_MATRIX)) #applying quantization 
            eBlock = encode_block(block)                    #scanning the matrix in zigzag and RL encoding it
            bytes = convertToByteArray(eBlock)              #converting to an array of array of bits
            for byte in bytes:
                stream.write_bits(byte)

def encode_header(header, stream):
    stream.write_bits(header)

def compressImage(filename, out_filename):
    img = cv2.imread(filename, 0)
    
    height, width = img.shape[:2]

    bytes_array = np.fromfile(filename, dtype = "uint8")
    bits = np.unpackbits(bytes_array)

    header = bits[:54*8]
    header = list(header)

    stream = OutputBitStream(out_filename)

    encode_header(header, stream)
    stream.flush()
    encode_pixels(img, [height, width], stream)
    stream.close()

def decode_block(stream):
    sequence = []

    numberCount = from_binary_list(stream.read_bits(8))
    sequence.append(numberCount)

    for i in range(numberCount):
        number = from_binary_list(stream.read_bits(8))
        sequence.append(number)
    zeroCount = from_binary_list(stream.read_bits(8))
    sequence.append(zeroCount)
    block = reverseRLE(sequence)
    block = reverseZigzag(block)
    return block
def decode_pixels(hw, stream):
    m = generateTransformMatrix()
    mt = np.transpose(m)
    height, width = hw
    nimg = np.zeros((width, height))
    for i in range(0, height, 8):
        for j in range(0, width, 8):
            block = decode_block(stream)
            idct = inverseDCT(QUANT_MATRIX, m, mt, block)

            block = np.uint8(np.around(idct))
            nimg[i:i+8, j:j+8] = block
    return nimg

def decompressImage(filename, out_filename):
    bytes_array = np.fromfile(filename, dtype = "uint8")
    bits = np.unpackbits(bytes_array)

    #WIDTH  =  (17*8):(21*8)
    #HEIGHT = (21*8):(25*8)
    header = bits[:54*8]
    w = header[(17*8):(21*8)]
    h = header[(21*8):(25*8)]
    width = from_binary_list(w)
    height = from_binary_list(h)
    
    stream = InputBitStream(filename)

    header = stream.read_bits(54*8)
    stream.flush()

    img = decode_pixels([height, width], stream)
    stream.flush()

    cv2.imwrite(out_filename, img)
    
def main():
    filename = 'lena512.bmp'
    c_filename = 'lena512.dct'
    out_filename = 'teste.bmp'

    compressImage(filename, c_filename)
    decompressImage(c_filename, out_filename)



if __name__ == '__main__':
    main()