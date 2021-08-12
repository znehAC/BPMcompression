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
  <a href="#-introçoes">Introduções</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
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

## 💻 Intruções

Para a execução do programa:

```bash
Baixar a code nas releases e seguir o passo á passo a seguir:

./codec <entrada> <saída> <método> <opção> 

<entrada> caminho da imagem a ser comprimida/descomprimida
<saída> caminho da imagem/arquivo que será criada

<método> huff para Huffman, dct para DCT
<opção> cod ou dec, cod para codificar e dec para decodificar. 

Exemplo: 
./codec imagem.bmp imagem.huff huff cod 

./codec imagem.huff imagem.bmp huff dec 
```

---

Feito por [Daniel Vitor](https://github.com/danielVFS) & [Adriano César](https://github.com/znehAC)
