# Scraping SIGAA UnB

Este projeto realiza web scraping do sistema SIGAA (Sistema Integrado de Gestão de Atividades Acadêmicas) da Universidade de Brasília para extrair informações sobre turmas disponíveis.

## Funcionalidades

Os scripts preenchem automaticamente o formulário no site do SIGAA com os seguintes valores:
- **Nível de Ensino**: GRADUAÇÃO
- **Unidade**: CAMPUS UNB GAMA-FACULDADE DE CIÊNCIAS E TECNOLOGIAS EM ENGENHARIA - BRASÍLIA
- **Ano-Período**: 2025-1

Em seguida, extraem os dados das turmas encontradas e os salvam em arquivos CSV.

## Versões Disponíveis

O projeto oferece duas implementações:

1. **scraping.py**: Utiliza BeautifulSoup e requests para fazer uma requisição HTTP simples.
2. **selenium_scraping.py**: Utiliza Selenium para controlar um navegador Chrome, ideal para sites que usam JavaScript para renderizar conteúdo.

## Requisitos

- Python 3.6 ou superior
- Bibliotecas Python listadas em `requirements.txt`
- Para a versão com Selenium: Chrome ou Chromium instalado no sistema

## Instalação

1. Clone este repositório ou baixe os arquivos.
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Uso

### Versão com BeautifulSoup

```bash
python scraping.py
```

### Versão com Selenium

```bash
python selenium_scraping.py
```

Ambos os scripts irão:
1. Acessar o site do SIGAA
2. Preencher o formulário com os valores configurados
3. Extrair os dados das turmas
4. Salvar os resultados em um arquivo CSV na pasta `dados/`

## Estrutura de Dados

O CSV resultante contém as seguintes colunas:
- `codigo`: Código da disciplina
- `disciplina`: Nome da disciplina
- `turma`: Número da turma
- `horario`: Horário das aulas
- `local`: Local onde as aulas ocorrem
- `docente`: Nome do professor responsável

## Resolução de Problemas

Se a versão com BeautifulSoup não funcionar, tente a versão com Selenium que é mais robusta para sites dinâmicos.

Para análise e depuração:
- A versão com BeautifulSoup gera um arquivo `response.html`
- A versão com Selenium gera os arquivos `selenium_response.html`, `antes_busca.png` e `resultados.png`

## Qual versão utilizar?

- **BeautifulSoup (scraping.py)**: Mais rápido e leve, ideal para sites com conteúdo estático.
- **Selenium (selenium_scraping.py)**: Mais robusto para sites que usam JavaScript para carregar dados dinamicamente ou quando há problemas com tokens de sessão.

## Nota Legal

Este script é apenas para fins educacionais. Respeite os termos de uso do site do SIGAA. 