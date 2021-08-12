from numpy.core.defchararray import index
import BitUtil as bitu
import numpy as np
from math import sqrt, cos, pi, floor
from cv2 import imread, imwrite

from numpy.core.fromnumeric import shape

# Matriz de quantizacao
QUANT_MATRIX = [[16, 11, 10, 16, 24, 40, 51, 61],
              [12, 12, 14, 19, 26, 58, 60, 55],
              [14, 13, 16, 24, 40, 57, 69, 56],
              [14, 17, 22, 29, 51, 87, 80, 62],
              [18, 22, 37, 56, 68, 109, 103, 77],
              [24, 35, 55, 64, 81, 104, 113, 92],
              [49, 64, 78, 87, 103, 121, 120, 101],
              [72, 92, 95, 98, 112, 100, 103, 99]]

# funcao para gerar valor da matriz DCT
def getTransformValue(i, j):
    if i == 0:
        return 1/sqrt(8)
    else:
        return (1/2)*cos(((2*j+1)*i*pi)/16)

# funcao que gera a matriz DCT
def generateTransformMatrix():
    M = np.zeros((8, 8))
    for i in range(8):
        for j in range(8):
            M[i][j] = getTransformValue(i, j)
    return M

# aplica a transformacao no bloco
def applyDCT(m, mt, block):
    return np.matmul(np.matmul(m, block), mt) # MxGxMT

# inverte a transformacao e quantizacao no bloco
def inverseDCT(qm, m, mt, block):
    for i in range(8):
        for j in range(8):
            block[i, j] = np.round(block[i, j]*qm[i][j]) # reverte a quantizacao
    return np.matmul(np.matmul(mt, block), m) # MTxGxM


def zigzag(m):
    count = 1 # numeros de elementos em uma coluna
    direction = -1 # indica a direcao da coluna
    result = []
    currentX = 0 # j
    currentY = 0 # i
    n = shape(m)[0]*2 - 1 #informa o numero de diagonais
    for i in range(n):
        for x in range(count): # percorre por uma diagonal
            result.append(int(m[currentY, currentX]))
            if x == count -1: # acabou os elementos na diagonal, para
                break
            elif direction == 1: # sobe na diagonal
                currentY -= 1
                currentX += 1
            elif direction == -1: # desce na diagonal
                currentY += 1
                currentX -= 1

        if i < floor(n/2) : # caso esteja em menos da metade das diagonais
            if direction == 1: # o proximo numero eh o da direita
                currentX += 1
                direction = -1 # direcao vai ser pra baixo
            elif direction == -1: # proximo numero eh o debaixo
                currentY += 1
                direction = 1
            count += 1 # aumenta o numero de elementos na diagonal
        else: # passou da metade das diagonais
            if direction == 1: # o proximo numero eh o debaixo
                currentY += 1
                direction = -1
            elif direction == -1: # proximo numero eh o da direita
                currentX += 1
                direction = 1
            count -= 1  # diminui o numero de elementos na diagonal
    return result

def reverseZigzag(zz):
    count = 1 # numero de elementos em uma diagonal
    arrayPosition = 0 # posicao do array
    direction = -1
    size = int(sqrt(len(zz))) # obtem o tamanho da matriz
    result = np.zeros((size, size))
    currentX = 0
    currentY = 0
    n = size*2 - 1
    for i in range(n):
        for x in range(count):
            result[currentY, currentX] = float(zz[arrayPosition]) # adiciona na matriz o elemento correspondente
            arrayPosition += 1 # proximo elemento
            if x == count -1:
                break
            elif direction == 1:
                currentY -= 1
                currentX += 1
            elif direction == -1:
                currentY += 1
                currentX -= 1

        if i < floor(n/2) :
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
    lastNonZero = 0 # numero do indice do ultimo elemento nao zero
    zerosCount = 0 
    result = []
    for i in range(len(array)-1, -1, -1): # percorre o array ao contrario
        if array[i] != 0:
            lastNonZero = i 
            break
        zerosCount += 1

    result.append(lastNonZero+1) # adiciona o numero de elementos nao zero no inicio do codigo

    for i in range(lastNonZero+1): # adiciona os elementos nao zeros
        result.append(array[i])

    result.append(zerosCount) # adiciona a quantidade de zeros
    return result

def reverseRLE(array):
    result = []
    zerosCount = array[len(array)-1] # obtem-se o numero de zeros

    for i in range(array[0]):
        result.append(array[i+1])

    for i in range(zerosCount):
        result.append(0)
    return result

def convertToByteArray(a):
    result = []
    for i in range(len(a)):
        if a[i] < 0: # caso o numero seja negativo converte ele para escrever
            a[i] = a[i]*-1
        result.append(bitu.pad_bits(bitu.to_binary_list(a[i]), 8)) # adiciona o numero em 8 bits
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
            
            block = img[i:i+8, j:j+8]                       # bloco com o tamanho 8x8
            dct = applyDCT(m, mt, block)                    # aplica o dct na matriz
            block = np.around(np.divide(dct, QUANT_MATRIX)) # aplica quantizacao 
            eBlock = encode_block(block)                    # performa o zigzag+rle no bloco
            bytes = convertToByteArray(eBlock)              # converto o array de ints em um array com 8 bits cada numero

            for byte in bytes:
                stream.write_bits(byte)

def encode_header(header, stream):
    stream.write_bits(header)

def decode_block(stream):
    sequence = []

    numberCount = bitu.from_binary_list(stream.read_bits(8)) # pega o numero de elementos nao zeros
    sequence.append(numberCount)

    for i in range(numberCount): # le todos os elementos nao zeros
        number = bitu.from_binary_list(stream.read_bits(8))
        sequence.append(number)

    zeroCount = bitu.from_binary_list(stream.read_bits(8))
    sequence.append(zeroCount)

    block = reverseRLE(sequence)
    block = reverseZigzag(block)
    return block

def decode_pixels(hw, stream):
    m = generateTransformMatrix()
    mt = np.transpose(m)
    height, width = hw
    nimg = np.zeros((height, width)) # matriz que representara a imagem

    for i in range(0, height, 8):
        for j in range(0, width, 8):
            block = decode_block(stream)
            idct = inverseDCT(QUANT_MATRIX, m, mt, block)

            block = np.uint8(np.around(idct))
            nimg[i:i+8, j:j+8] = block
    return nimg

def compressImage(filename, out_filename):
    img = imread(filename, 0) # aqui eh utilizado o opencv para ler a imagem em uma matriz
    
    height, width = img.shape[:2]

    bytes_array = np.fromfile(filename, dtype = "uint8")
    bits = np.unpackbits(bytes_array)

    header = bits[:54*8]
    header = list(header)

    stream = bitu.OutputBitStream(out_filename)

    encode_header(header, stream)
    stream.flush()

    encode_pixels(img, [height, width], stream)
    stream.close()
    
def decompressImage(filename, out_filename):
    bytes_array = np.fromfile(filename, dtype = "uint8")
    bits = np.unpackbits(bytes_array)

    #WIDTH  =  (17*8):(21*8)
    #HEIGHT = (21*8):(25*8)
    header = bits[:54*8]
    w = header[(17*8):(21*8)]
    h = header[(21*8):(25*8)]
    width = bitu.from_binary_list(w)
    height = bitu.from_binary_list(h)
    
    stream = bitu.InputBitStream(filename)

    header = stream.read_bits(54*8)
    stream.flush()
    img = decode_pixels([height, width], stream)
    stream.flush()

    imwrite(out_filename, img) # opencv utilizado para escrever a matriz que representa a imagem
    
