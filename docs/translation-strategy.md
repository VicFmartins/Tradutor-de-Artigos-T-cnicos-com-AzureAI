# Estrategia de traducao

O projeto foi desenhado para traduzir artigos tecnicos sem estragar elementos importantes do texto.

## O que e protegido

- blocos de codigo com fence
- trechos inline com crases
- termos tecnicos definidos em `preserve_terms`
- glossario customizado informado pelo usuario

## Como o fluxo funciona

1. O conteudo passa por protecao de codigo.
2. O markdown e dividido em chunks menores.
3. Se o Azure Translator estiver configurado, o texto vai para a API com dynamic dictionary.
4. Se nao estiver configurado, o projeto entra em modo `local_preview`.
5. O resultado final restaura os blocos de codigo originais.

## Quando usar o modo local

O modo local e util para:

- demonstrar o pipeline sem credenciais
- validar preprocessamento e preservacao de termos
- testar payloads e integracao da API

Ele nao substitui traducao real de alta qualidade.
