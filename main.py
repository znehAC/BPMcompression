from os import name, write
import numpy as np
from PIL import Image
from numpy.core.fromnumeric import sort

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







def build_tree(counts) :
    nodes = [entry[::-1] for entry in counts] # Reverse each (symbol,count) tuple
    while len(nodes) > 1 :
        leastTwo = tuple(nodes[0:2]) # get the 2 to combine
        theRest = nodes[2:] # all the others
        combFreq = leastTwo[0][0] + leastTwo[1][0]  # the branch points freq
        nodes = theRest + [(combFreq, leastTwo)] # add branch point to the end
        nodes = sorted(nodes, key=lambda x: x[0]) # sort it into place
    return nodes[0] # Return the single tree inside the list


def trim_tree(tree) :
    p = tree[1] # Ignore freq count in [0]
    if type(p) is tuple: # Node, trim left then right and recombine
        return (trim_tree(p[0]), trim_tree(p[1]))
    return p # Leaf, just return it



def assign_codes_impl(codes, node, pat):
    if type(node) == tuple:
        assign_codes_impl(codes, node[0], pat + [0]) # Branch point. Do the left branch
        assign_codes_impl(codes, node[1], pat + [1]) # then do the right branch.
    else:
        codes[node] = pat # A leaf. set its code

def assign_codes(tree):
    codes = {}
    assign_codes_impl(codes, tree, [])
    return codes


def encode_header(header, bitstream):
    bitstream.write_bits(header)   

def encode_tree(tree, bitstream):
    if type(tree) == tuple: # Note - write 0 and encode children
        bitstream.write_bit(0)
        encode_tree(tree[0], bitstream)
        encode_tree(tree[1], bitstream)
    else: # Leaf - write 1, followed by 8 bit symbol
        bitstream.write_bit(1)
        symbol_bits = pad_bits(to_binary_list(tree), 8)
        bitstream.write_bits(symbol_bits)


def encode_pixels(image, codes, bitstream):
    for pixel in image.getdata():
            bitstream.write_bits(codes[pixel])

def count_symbols(pixels):
    symbols = dict()
    for pixel in pixels:
        if pixel in symbols:
            # print(f'ja estava no dic')
            symbols[pixel] += 1
        else:
            symbols[pixel] = 1

    symbols = sorted(symbols.items(), key =
             lambda kv:(kv[1], kv[0]))

    return symbols

def compressImage(filename, out_filename):
    bytes_array = np.fromfile(filename, dtype = "uint8")
    bits = np.unpackbits(bytes_array)

    #WIDTH  =  (17*8):(21*8)
    #HEIGHT = (21*8):(25*8)
    header = bits[:54*8]

    header = list(header)
    pixels = bytes_array[54:]

    symbols = count_symbols(pixels)

    tree = build_tree(symbols)

    t_tree = trim_tree(tree)
    
    codes = assign_codes(t_tree)

    stream = OutputBitStream(out_filename)

    encode_header(header, stream)
    stream.flush()

    encode_tree(t_tree, stream)
    stream.flush()

    image = Image.open(filename)
    encode_pixels(image, codes, stream)
    stream.close()

def decode_tree(bitstream):
    flag = bitstream.read_bits(1)[0]
    if flag == 1: # Leaf, read and return symbol
        return from_binary_list(bitstream.read_bits(8))
    left = decode_tree(bitstream)
    right = decode_tree(bitstream)
    return (left, right)

def decode_value(tree, bitstream):
    bit = bitstream.read_bits(1)[0]
    node = tree[bit]
    if type(node) == tuple:
        return decode_value(node, bitstream)
    return node

def decode_pixels(height, width, tree, bitstream):
    pixels = bytearray()
    for i in range(height * width):
        pixels.append(decode_value(tree, bitstream))
    return Image.frombytes('L', (width, height), bytes(pixels))

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

    t_tree = decode_tree(stream)
    stream.flush()

    image = decode_pixels(height, width, t_tree, stream)
    stream.close()

    image.save(out_filename)

if __name__ == "__main__":
    original_file = "DesertGray.bmp"
    compressed_file = "DesertGray_c.file"
    decompressed_file = "DesertGray_d.bmp"


    compressImage(original_file, compressed_file)
    decompressImage(compressed_file, decompressed_file)
    
 