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


---

# **Documentação do Projeto: Recomendador de Disciplinas da UnB**

## **1. Visão Geral**
Este projeto tem como objetivo recomendar automaticamente disciplinas da Universidade de Brasília (UnB) para os alunos, utilizando inteligência artificial generativa da AWS Bedrock. O sistema recebe como entrada o curso do usuário e suas áreas de interesse e, com base nesses dados, sugere disciplinas relevantes.

## **2. Arquitetura do Sistema**

### **2.1. Componentes Principais**

1. **Raspagem de Dados (Web Scraping)**
   - Extrai informações sobre as disciplinas e seus respectivos cursos do SIGAA.
   - Obtém a descrição de cada disciplina e os cursos oferecidos na UnB.
   
2. **Armazenamento de Dados (Amazon S3)**
   - Os dados extraídos do SIGAA são armazenados no Amazon S3.
   - Esses dados servirão como base de conhecimento para o modelo de IA.

3. **Base de Conhecimento**
   - Estruturamos os dados coletados para facilitar a consulta.
   - A base de conhecimento contém informações organizadas sobre as disciplinas e suas descrições.

4. **Módulo de IA Generativa (AWS Bedrock)**
   - Um sistema multiagente processa a base de conhecimento para gerar recomendações:
     - **Agente 1**: Identifica disciplinas relevantes com base no curso e nos interesses do aluno.
     - **Agente 2**: Recupera a descrição detalhada de cada disciplina sugerida.

5. **Interface do Usuário (Streamlit)**
   - Interface web responsiva onde o aluno informa seu curso e áreas de interesse.
   - Conecta-se ao serviço de IA para obter as recomendações e exibir os resultados.

6. **Pipeline de Processamento**
   - Automatiza a atualização dos dados no S3 e a estruturação da base de conhecimento.
   - Garante que o modelo de IA tenha sempre informações atualizadas.

### **2.2. Fluxo de Dados**
1. O sistema realiza a raspagem dos dados do SIGAA.
2. As informações extraídas (disciplinas e descrições) são armazenadas no Amazon S3.
3. Um pipeline de processamento organiza esses dados e os transforma em uma base de conhecimento.
4. O AWS Bedrock consulta essa base e executa o processo multiagente para gerar recomendações.
5. A interface do usuário (Streamlit) captura os inputs do aluno e solicita recomendações ao AWS Bedrock.
6. Os resultados são retornados e exibidos para o aluno.

## **3. Diagrama da Arquitetura**

```plaintext
+-----------------------------------------------------+
|                   Usuário                          |
|    (Acessa Streamlit e fornece inputs)            |
+-----------------------------------------------------+
                          |
                          v
+-----------------------------------------------------+
|            Interface do Usuário (Streamlit)        |
|  - Coleta curso e interesses do usuário           |
|  - Envia requisição para AWS Bedrock              |
|  - Exibe disciplinas recomendadas                 |
+-----------------------------------------------------+
                          |
                          v
+-----------------------------------------------------+
|        Serviço de IA Generativa (AWS Bedrock)      |
|  - Multiagente processa a requisição              |
|  - Agente 1: Busca disciplinas relevantes         |
|  - Agente 2: Retorna descrição detalhada          |
+-----------------------------------------------------+
                          |
                          v
+-----------------------------------------------------+
|          Base de Conhecimento (AWS S3)            |
|  - Contém disciplinas e descrições                |
|  - Alimentada pelo pipeline de dados              |
+-----------------------------------------------------+
                          ^
                          |
+-----------------------------------------------------+
|         Pipeline de Processamento                 |
|  - Extrai dados do S3 e estrutura para IA         |
+-----------------------------------------------------+
                          ^
                          |
+-----------------------------------------------------+
|          Raspagem de Dados (SIGAA)                |
|  - Coleta cursos e disciplinas da UnB             |
|  - Armazena no S3                                 |
+-----------------------------------------------------+
```

## **4. Tecnologias Utilizadas**
- **AWS Bedrock**: Motor de IA generativa para processar recomendações.
- **Amazon S3**: Armazenamento de dados estruturados.
- **Streamlit**: Interface interativa para os alunos.
- **Python (BeautifulSoup, Scrapy, Requests)**: Raspagem de dados do SIGAA.
- **Pandas, JSON**: Manipulação e formatação dos dados.

## **5. Benefícios do Sistema**
- Automatiza a sugestão de disciplinas relevantes para os alunos.
- Facilita a escolha de matérias alinhadas aos interesses acadêmicos.
- Mantém os dados sempre atualizados através de um pipeline automatizado.
- Utiliza IA generativa para oferecer recomendações personalizadas.

## **6. Considerações Finais**
Este sistema visa facilitar a vida acadêmica dos alunos da UnB, oferecendo sugestões personalizadas de disciplinas com base no perfil de cada estudante. Com o uso de IA generativa da AWS Bedrock e um pipeline de processamento automatizado, garantimos um fluxo eficiente e sempre atualizado para a recomendação de matérias.

