<h1 align="center">
    Trabalho de Compressão: DCT + Huffman
</h1>

<h3 align="center">
  Alunos: Adriano César | Daniel Vitor
</h3>

<h3 align="center">
  Link da apresentação: https://drive.google.com/file/d/1OZj8YKfZMbjwICJAVYQjzWL43IhcLZ9v/view?usp=sharing
</h3>

<p align="center">
  <a href="#rocket-passo-á-passo">Passo á Passo</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#-compressão-e-descompressão">Compressão e Descompressão</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
</p>

<br>

## :rocket: Passo á Passo

- **Huffman**:

  - O algoritmo de Huffman recebe um fluxo de bits e devolve um fluxo de bits comprimido que representa o fluxo original. Em geral, o fluxo comprimido é mais curto que o original.
  - Para ser feito a compressão, são realizados os passos:

    1. São contados quantos símbolos(Folhas) contem o arquivo;
    2. Com os símbolos, agora é criada a arvoré binária com as probabilidades de cada símbolo;
    3. Tendo a árvore, próximo passo é podá-la;
    4. Agora entra o Encoding;
       - Temos a função encode para retornar os valores de cada símbolo.
       - É pego a stream de bits;
       - Encode do Header, da árvore e dos pixels da imagem.
       - O bitstream é escrito em um arquivo.
    5. Agora o Decoding;

- **DCT**:
  1. É aplicado o DCT, seguido da quantização.
  2. É feito o zigzag;
  3. É feito o Encoding da imagem e o bitstream é escrito em um arquivo.
  4. To be continued...

## 💻 Compressão e Descompressão

Para a compresão de **Huffman**:

```bash
Arquivo de Entrada: lena512.bmp
Arquivo comprimido: lena512.file
Arquivo descomprimido: lena512_d.bmp
```

Para a compresão **DCT**:

```bash
Arquivo de Entrada: lena512.bmp
Arquivo de Saída: teste.bmp
```

---

Feito por [Daniel Vitor](https://github.com/danielVFS) & [Adriano César](https://github.com/znehAC)
