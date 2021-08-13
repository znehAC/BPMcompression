from numpy.core.defchararray import index
import BitUtil as bitu
import numpy as np
from math import sqrt, cos, pi, floor, pow
from cv2 import imread, imwrite

from numpy.core.fromnumeric import shape

# Matriz de quantizacao
QUANT_MATRIX = [[3, 2, 2, 3, 5, 8, 10, 12],
                [2, 2, 3, 4, 5, 12, 12, 11 ],
                [3, 3, 3, 5, 8, 11, 14, 11 ],
                [3, 3, 4, 6, 10, 17, 16, 12 ],
                [4, 4, 7, 11, 14, 22, 21, 15 ],
                [5, 7, 11, 13, 16, 21, 23, 18 ],
                [10, 13, 16, 17, 21, 24, 24, 20 ],
                [14, 18, 19, 20, 22, 20, 21, 20 ]]


def getQuantMatrix(quality):
    quality = (13-quality)+1 # aumenta o numero final em 4, pois valores abaixo de 5 geram artefatos
    qt = np.zeros((8,8))
    for i in range(len(QUANT_MATRIX[0])):
        for j in range(len(QUANT_MATRIX[0])):
            qt[i][j] = QUANT_MATRIX[i][j] * quality
    return qt

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
    x = np.zeros((shape(block)[0], shape(block)[1]))
    for i in range(8):
        for j in range(8):
            x[i, j] = np.round(block[i, j]*qm[i][j]) # reverte a quantizacao
    return np.matmul(np.matmul(mt, x), m) # MTxGxM


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
        a[i] = np.uint8(a[i])
        result.append(bitu.pad_bits(bitu.to_binary_list(a[i]), 8)) # adiciona o numero em 8 bits
    return result

def encode_block(block):
    zz = zigzag(block)
    rle = rLEncode(zz)
    return rle

# get the squared error sum of matrix X and Y
def getBlockSE(x, y):
    sum = 0
    for i in range(8):
        for j in range(8):
            sum += (x[i, j] - y[i, j])*(x[i, j] - y[i, j])
    return sum

def encode_pixels(img, hw, stream, quality):
    m = generateTransformMatrix()
    mt = np.transpose(m)
    qm = getQuantMatrix(quality)
    height, width = hw
    seSum = 0
    for i in range(0, height, 8):
        for j in range(0, width, 8):
            
            block = img[i:i+8, j:j+8]                       # bloco com o tamanho 8x8
            dct = applyDCT(m, mt, block)                    # aplica o dct na matriz
            dct = np.around(np.divide(dct, qm))             # aplica quantizacao 
            idct = inverseDCT(qm, m, mt, dct)
            seSum += getBlockSE(block, idct)
            eBlock = encode_block(dct)                      # performa o zigzag+rle no bloco
            bytes = convertToByteArray(eBlock)              # converto o array de ints em um array com 8 bits cada numero

            for byte in bytes:
                stream.write_bits(byte)
    
    mse = seSum/(height*width)
    psnr = 255/mse
    return [mse, psnr]

def encode_header(header, stream):
    stream.write_bits(header)

def decode_block(stream):
    sequence = []

    numberCount = bitu.from_binary_list(stream.read_bits(8)) # pega o numero de elementos nao zeros
    numberCount = np.int8(numberCount)
    sequence.append(numberCount)

    for i in range(numberCount): # le todos os elementos nao zeros
        number = bitu.from_binary_list(stream.read_bits(8))
        number = np.int8(number)
        sequence.append(number)

    zeroCount = bitu.from_binary_list(stream.read_bits(8))
    sequence.append(zeroCount)

    block = reverseRLE(sequence)
    block = reverseZigzag(block)
    return block

def decode_pixels(hw, stream, quality):
    m = generateTransformMatrix()
    mt = np.transpose(m)
    qt = getQuantMatrix(quality)
    height, width = hw
    nimg = np.zeros((height, width)) # matriz que representara a imagem

    for i in range(0, height, 8):
        for j in range(0, width, 8):
            block = decode_block(stream)
            idct = inverseDCT(qt, m, mt, block)

            block = np.uint8(np.around(idct))
            nimg[i:i+8, j:j+8] = block
    return nimg

def compressImage(filename, out_filename, quality):
    img = imread(filename, 0) # aqui eh utilizado o opencv para ler a imagem em uma matriz
    
    height, width = img.shape[:2]

    bytes_array = np.fromfile(filename, dtype = "uint8")
    bits = np.unpackbits(bytes_array)

    header = bits[:54*8]
    header = list(header)
    q_header = bitu.pad_bits(bitu.to_binary_list(quality), 8)
    header += q_header

    
    stream = bitu.OutputBitStream(out_filename)

    encode_header(header, stream)
    stream.flush()

    mse, psnr = encode_pixels(img, [height, width], stream, quality)
    stream.close()
    
    return [mse, psnr]
    
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
    quality = stream.read_bits(8)
    quality = bitu.from_binary_list(quality)
  
    
    stream.flush()
    img = decode_pixels([height, width], stream, quality)
    stream.flush()

    imwrite(out_filename, img) # opencv utilizado para escrever a matriz que representa a imagem
    


def main():
    compressImage('lena512.bmp', 'lena512.dct', 4)
    decompressImage('lena512.dct', 'lena512d.bmp')
        
if __name__ == '__main__':
    main()