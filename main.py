import huffman as huff
import dct
from sys import argv
from time import time

HUFF = 'huff'
DCT = 'dct'
DEC = 'dec'
COD = 'cod'

MESSAGES = {
     0: '',
    -1: '\nArgumentos insuficientes ou inválidos.',
    -2: '\nMétodo inserido inválido.',
    -3: '\nOpção inserida inválida.'
}

def checkArguments(args):
    if args[0].lower() == '-h':
        return 1
    if len(args) < 4:
        return -1
    if args[2].lower() != HUFF and args[2].lower() != DCT:
        return -2
    if args[3].lower() != DEC and args[3].lower() != COD:
        return -3
    return 0

def printHelpMessage():
    pass

def validateInput(args):
    code = checkArguments(args)
    if code == 0:
        return True
    elif code == 1:
        printHelpMessage()
        return False
    else:
        print(MESSAGES[code])
        print('Para mais informações leia Readme.txt ou use o comando -h.\n')
        return False

def getOperation(metOp):
    met, op = metOp
    code = 0
    if met.lower() == HUFF:
        code += 1
    elif met.lower() == DCT:
        code += 3
    if op.lower() == DEC:
        code += 1
    elif op.lower() == COD:
        code += 2
    return code

def start(opType, imageInput, output):
    operation = getOperation(opType)
    start_time = time()
    if operation == 2:
        print(f'\nDescomprimindo o arquivo {imageInput} ao arquivo {output}')
        print('\nMétodo: Huffman')

        huff.decompressImage(imageInput, output)

        print(f'\nDescompressão terminada, tempo: {time()-start_time}\n')
    elif operation == 3:
        print(f'\nComprimindo o arquivo {imageInput} ao arquivo {output}')
        print('\nMétodo: Huffman')

        huff.compressImage(imageInput, output)
        print(f'\nCompressão terminada, tempo: {time()-start_time}\n')
    elif operation == 4:
        print(f'\nDescomprimindo o arquivo {imageInput} ao arquivo {output}')
        print('\nMétodo: DCT')

        dct.decompressImage(imageInput, output)
        print(f'\nDescompressão terminada, tempo: {time()-start_time}\n')
    elif operation == 5:
        quality = int(input('\nInsira o nivel de qualidade que gostaria na imagem (4 - 9)\n=> '))
        start_time = time()
        print(f'\nComprimindo o arquivo {imageInput} ao arquivo {output}')
        print('\nMétodo: DCT')

        dct.compressImage(imageInput, output, quality)
        print(f'\nCompressão terminada, tempo: {time()-start_time}\n')

def main():
    args = argv[1:]
    if validateInput(args):
        start(args[2:], args[0], args[1])
        
if __name__ == '__main__':
    main()
