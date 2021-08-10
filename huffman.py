from os import name, write
import numpy as np
from PIL import Image
from numpy.core.fromnumeric import sort
import BitUtil as bitu

def build_tree(counts) :
    nodes = [entry[::-1] for entry in counts] # inverte a tupla para (symbol, count)
    while len(nodes) > 1 :
        leastTwo = tuple(nodes[0:2]) # pega os primeiros 2, ja que esta invertido
        theRest = nodes[2:] 
        combFreq = leastTwo[0][0] + leastTwo[1][0]  # soma a contagem dos dois
        nodes = theRest + [(combFreq, leastTwo)] # adiciona no final
        nodes = sorted(nodes, key=lambda x: x[0]) # reordena a lista denovo
    return nodes[0] # retorna a arvore agora presente na primeira posicao

def trim_tree(tree) :
    p = tree[1] # nao precisa da frequencia da raiz
    if type(p) is tuple: # nao eh uma folha, corta pra esquerda depois pra direita
        return (trim_tree(p[0]), trim_tree(p[1])) # a arvore vai ser retornada em uma tupla (noEsquerdo, noDireito)
    return p # eh uma folham retorno ela

def assign_codes_impl(codes, node, code):
    if type(node) == tuple: # nao eh uma folha (tem filhos)
        assign_codes_impl(codes, node[0], code + [0]) # vou pra esquerda, entao adiciono 0
        assign_codes_impl(codes, node[1], code + [1]) # vou pra direita, adiciono 1
    else:
        codes[node] = code # uma folha, assinalo um codigo a ela no dicionario codes

def assign_codes(tree):
    codes = {} # uma lista de codigos inicial vazia
    assign_codes_impl(codes, tree, []) # a arvore eh a "podada"
    return codes

def encode_header(header, bitstream):
    bitstream.write_bits(header)   

def encode_tree(tree, bitstream):
    if type(tree) == tuple: # nao eh folha, escreve 0 e vai para os filhos
        bitstream.write_bit(0)
        encode_tree(tree[0], bitstream) #filho a esquerda
        encode_tree(tree[1], bitstream) #filho a direita
    else: # eh uma folha, escreve 1 e o valor (Byte do pixel) em 1 byte
        bitstream.write_bit(1)
        symbol_bits = bitu.pad_bits(bitu.to_binary_list(tree), 8)
        bitstream.write_bits(symbol_bits)

def encode_pixels(image, codes, bitstream):
    for pixel in image.getdata():   # utiliza aqui o modulo PIL, com a classe Imagem, o .getData() da os pixels
            bitstream.write_bits(codes[pixel]) # escreve o codigo correspondente do pixel

def count_symbols(pixels):
    symbols = dict() 
    for pixel in pixels:
        if pixel in symbols: # faz uma checagem se o pixel ja foi contado antes
            symbols[pixel] += 1 # adiciona mais um na frequencia dele
        else:
            symbols[pixel] = 1 # inicializa ele no dicionario 

    symbols = sorted(symbols.items(), key =
             lambda kv:(kv[1], kv[0]))  # reordena o dicionario com base na frequencia
    return symbols


def decode_tree(bitstream):
    type = bitstream.read_bits(1)[0]
    if type == 1: # eh uma folha
        return bitu.from_binary_list(bitstream.read_bits(8)) # le e retorna o byte
    left = decode_tree(bitstream) # le se a arvore da esquerda
    right = decode_tree(bitstream) # e entao a arvore da direita, ja que foi codificado assim
    return (left, right)

def decode_value(tree, bitstream):
    bit = bitstream.read_bits(1)[0]
    node = tree[bit] # pega a posicao da esquerda ou direita na tupla
    if type(node) == tuple: # nao eh um no folha
        return decode_value(node, bitstream) # busca novamente na subarvore ate achar o no folha
    return node # eh a folha

def decode_pixels(height, width, tree, bitstream):
    pixels = bytearray() 
    for i in range(height * width):
        pixels.append(decode_value(tree, bitstream))
    return Image.frombytes('L', (width, height), bytes(pixels)) # retorna uma imagem do tipo gray scale 8 bits

def compressImage(filename, out_filename):
    bytes_array = np.fromfile(filename, dtype = "uint8") # funcao do numpy que le um arquivo e pega os bytes
    bits = np.unpackbits(bytes_array) # funcao que transforma os bytes em bits

    header = bits[:54*8] # pega os bits do header
    header = list(header)

    pixels = bytes_array[54:] # pega os bytes dos pixels

    symbols = count_symbols(pixels)

    tree = build_tree(symbols)

    t_tree = trim_tree(tree)
    
    codes = assign_codes(t_tree)

    stream = bitu.OutputBitStream(out_filename)

    encode_header(header, stream)
    stream.flush()

    encode_tree(t_tree, stream)
    stream.flush()

    image = Image.open(filename) # classe que permite ler os pixels de uma imagem
    encode_pixels(image, codes, stream)
    stream.close()
    
def decompressImage(filename, out_filename):
    bytes_array = np.fromfile(filename, dtype = "uint8") # classe utilizada para ler os bytes do arquivo
    bits = np.unpackbits(bytes_array) # utilizado para transformar em bits

    header = bits[:54*8] # le se o header da imagem
    w = header[(17*8):(21*8)]
    h = header[(21*8):(25*8)]
    width = bitu.from_binary_list(w)
    height = bitu.from_binary_list(h)
    
    stream = bitu.InputBitStream(filename) 
    header = stream.read_bits(54*8) # le 54 bytes para mover o "ponteiro" da stream de bits
    stream.flush()

    t_tree = decode_tree(stream)
    stream.flush()

    image = decode_pixels(height, width, t_tree, stream)
    stream.close()

    image.save(out_filename) # classe que salva determinada imagem

 