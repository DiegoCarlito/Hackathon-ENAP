import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from urllib.parse import urljoin
import os
import re


def coleta_dados(session, component_id, viewstate, base_url, debug=False):
    """
    Função para obter os detalhes de um componente curricular
    acessando a página de detalhes do componente

    Args:
        session: Sessão HTTP
        component_id: ID do componente curricular
        viewstate: ViewState para o formulário JSF
        base_url: URL base do SIGAA
        debug: Se True, salva a resposta HTML em um arquivo para debug

    Returns:
        Dicionário com os detalhes do componente curricular
    """
    print(
        f"[{time.strftime('%H:%M:%S')}] Acessando detalhes do componente ID: {component_id}..."
    )

    # A URL é a mesma da página principal, pois o site usa JavaScript para fazer a requisição AJAX
    details_url = base_url

    # Preparar dados para requisição POST baseado no que vemos no onclick do link
    form_data = {
        "formTurma": "formTurma",
        "formTurma:aqui": "formTurma:aqui",
        "id": component_id,
        "publico": "public",
        "javax.faces.ViewState": viewstate,
    }

    try:
        # Enviar requisição para obter os detalhes do componente
        print(
            f"[{time.strftime('%H:%M:%S')}] Enviando POST para obter detalhes do componente..."
        )
        response = session.post(details_url, data=form_data, timeout=30)

        # Salvar a resposta para debug somente se o flag debug estiver ativo
        if debug:
            with open(
                f"componente_{component_id}_response.html", "w", encoding="utf-8"
            ) as f:
                f.write(response.text)

        if response.status_code != 200:
            print(
                f"[{time.strftime('%H:%M:%S')}] ERRO ao acessar detalhes do componente: Status {response.status_code}"
            )
            return {}

        # Parsear o HTML da página de detalhes
        details_soup = BeautifulSoup(response.text, "html.parser")

        # Verificar se o HTML foi carregado corretamente
        if not details_soup or not details_soup.find_all():
            print(
                f"[{time.strftime('%H:%M:%S')}] ERRO: Não foi possível carregar o HTML da página de detalhes do componente."
            )
            return {}

        # Inicializar dicionário para armazenar os dados extraídos
        details = {}
        ementa = ""

        # Procurar tabela principal com as informações do componente
        dados_gerais_table = details_soup.find("table", {"class": "visualizacao"})

        if dados_gerais_table:
            print(f"[{time.strftime('%H:%M:%S')}] Tabela de dados gerais encontrada.")

            # Extrair dados da tabela
            rows = dados_gerais_table.find_all("tr")
            for row in rows:
                th_element = row.find("th")
                td_element = row.find("td")

                if th_element and td_element:
                    # Extrair rótulo e valor
                    label = th_element.text.strip()
                    if label.endswith(":"):
                        label = label[:-1]
                    value = td_element.text.strip()

                    # Adicionar ao dicionário de detalhes
                    details[label] = value

                    # Capturar a ementa separadamente
                    if "Ementa/Descrição" in label:
                        ementa = value
                        print(
                            f"[{time.strftime('%H:%M:%S')}] Ementa encontrada: {ementa[:50]}..."
                        )

        # Se não encontrou a tabela principal, tentar métodos alternativos
        if not details:
            print(
                f"[{time.strftime('%H:%M:%S')}] Tentando métodos alternativos para encontrar dados..."
            )

            # Método alternativo: procurar por todas as tabelas
            tables = details_soup.find_all("table")
            for table in tables:
                # Verificar se é a tabela de dados gerais
                header = table.find("tr", {"class": "linhaTitulo"})
                if header and "Dados Gerais do Componente Curricular" in header.text:
                    rows = table.find_all("tr")
                    for row in rows:
                        cells = row.find_all(["th", "td"])
                        if len(cells) >= 2:
                            label = cells[0].text.strip()
                            if label.endswith(":"):
                                label = label[:-1]
                            value = cells[1].text.strip()
                            details[label] = value

                            # Verificar se é a ementa
                            if "Ementa" in label or "Descrição" in label:
                                ementa = value

        # Extrair campos específicos e montar o dicionário de retorno
        component_details = {
            "tipo_componente": details.get(
                "Tipo do Componente Curricular", "Não informado"
            ),
            "modalidade_educacao": details.get(
                "Modalidade de Educação", "Não informado"
            ),
            "unidade_responsavel": details.get("Unidade Responsável", "Não informado"),
            "codigo_componente": details.get("Código", "Não informado"),
            "nome_componente": details.get("Nome", "Não informado"),
            "pre_requisitos": details.get("Pré-Requisitos", "Não informado"),
            "co_requisitos": details.get("Co-Requisitos", "Não informado"),
            "equivalencias": details.get("Equivalências", "Não informado"),
            "excluir_avaliacao": details.get(
                "Excluir da Avaliação Institucional", "Não informado"
            ),
            "matriculavel_online": details.get("Matriculável On-Line", "Não informado"),
            "horario_flexivel": details.get(
                "Horário Flexível da Turma", "Não informado"
            ),
            "permite_multiplas_aprovacoes": details.get(
                "Permite Múltiplas Aprovações", "Não informado"
            ),
            "quantidade_avaliacoes": details.get(
                "Quantidade de Avaliações", "Não informado"
            ),
            "ementa": ementa or details.get("Ementa/Descrição", "Não informado"),
            "carga_horaria_total": details.get(
                "Total de Carga Horária do Componente", "Não informado"
            ),
        }

        print(
            f"[{time.strftime('%H:%M:%S')}] Detalhes do componente {component_id} extraídos com sucesso!"
        )
        return component_details

    except Exception as e:
        print(
            f"[{time.strftime('%H:%M:%S')}] ERRO ao processar detalhes do componente: {str(e)}"
        )
        import traceback

        traceback.print_exc()
        return {}


def scrape_unb_classes(debug=False):
    """
    Função para fazer scraping das turmas da UnB no SIGAA,
    preenchendo automaticamente o formulário com os campos:
    - Nível de Ensino: GRADUAÇÃO (valor "G")
    - Unidade: CAMPUS UNB GAMA: FACULDADE DE CIÊNCIAS E TECNOLOGIAS EM ENGENHARIA - BRASÍLIA (valor "673")
    - Ano-Período: 2025-1

    Args:
        debug: Se True, salva as respostas HTML em arquivos para debug
    """
    print("\n====== INICIANDO SCRAPING DAS TURMAS DA UNB ======")
    print(f"[{time.strftime('%H:%M:%S')}] Processo iniciado")

    # URL base do sistema SIGAA
    base_url = "https://sigaa.unb.br/sigaa/public/turmas/listar.jsf"

    # Fazendo a primeira requisição para obter os cookies e tokens
    session = requests.Session()

    try:
        print(f"[{time.strftime('%H:%M:%S')}] Enviando requisição GET inicial...")
        response = session.get(base_url, timeout=30)
        if response.status_code != 200:
            print(
                f"[{time.strftime('%H:%M:%S')}] ERRO: Status da resposta: {response.status_code}"
            )
            return None
    except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%H:%M:%S')}] ERRO ao acessar o site: {str(e)}")
        return None

    # Parsear o HTML da página
    soup = BeautifulSoup(response.text, "html.parser")

    # Extrair o viewstate (necessário para o formulário)
    print(f"[{time.strftime('%H:%M:%S')}] Buscando ViewState no formulário...")
    viewstate_element = soup.find("input", {"name": "javax.faces.ViewState"})

    if not viewstate_element:
        print(f"[{time.strftime('%H:%M:%S')}] ERRO: ViewState não encontrado.")
        # Salvar o HTML para diagnóstico
        with open("erro_sem_viewstate.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        return None

    viewstate = viewstate_element["value"]

    # Identificar o ID do formulário e dos campos
    form = soup.find("form", {"id": "formTurma"})
    if not form:
        print(f"[{time.strftime('%H:%M:%S')}] ERRO: Formulário não encontrado.")
        with open("erro_sem_form.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        return None

    # Obter o ID do botão de busca
    buscar_button = form.find("input", {"value": "Buscar"})
    if not buscar_button:
        print(f"[{time.strftime('%H:%M:%S')}] ERRO: Botão de busca não encontrado.")
        with open("erro_sem_botao.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        return None

    buscar_id = buscar_button.get("id", "formTurma:j_id_jsp_1370969402_11")

    # Com base no HTML fornecido, sabemos os valores exatos para o dropdown
    print(f"[{time.strftime('%H:%M:%S')}] Montando dados do formulário...")

    # Preparar os dados do formulário com os valores exatos
    form_data = {
        "formTurma": "formTurma",
        "formTurma:inputNivel": "G",  # Valor para GRADUAÇÃO conforme HTML
        "formTurma:inputDepto": "673",  # Valor para CAMPUS UNB GAMA conforme HTML
        "formTurma:inputAno": "2025",
        "formTurma:inputPeriodo": "1",
        buscar_id: "Buscar",
        "javax.faces.ViewState": viewstate,
    }

    print(
        f"[{time.strftime('%H:%M:%S')}] Parâmetros da busca: GRADUAÇÃO, CAMPUS UNB GAMA, 2025-1"
    )

    # Realizar a busca (enviar o formulário)
    print(f"[{time.strftime('%H:%M:%S')}] ENVIANDO FORMULÁRIO DE BUSCA...")
    try:
        search_response = session.post(base_url, data=form_data, timeout=60)
        if search_response.status_code != 200:
            print(
                f"[{time.strftime('%H:%M:%S')}] ERRO: Status da resposta POST: {search_response.status_code}"
            )
            return None
    except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%H:%M:%S')}] ERRO ao enviar o formulário: {str(e)}")
        return None

    # Salvar a resposta para depuração, se necessário
    if debug:
        with open("response.html", "w", encoding="utf-8") as f:
            f.write(search_response.text)

    # Parsear os resultados
    results_soup = BeautifulSoup(search_response.text, "html.parser")

    # Verificar se existem resultados
    if "Nenhuma turma encontrada" in search_response.text:
        print(
            f"[{time.strftime('%H:%M:%S')}] AVISO: Nenhuma turma encontrada com os critérios informados."
        )
        return None

    # Extrair tabela de resultados
    tables = results_soup.find_all("table", {"class": "listagem"})

    if not tables:
        print(
            f"[{time.strftime('%H:%M:%S')}] ERRO: Tabela de resultados não encontrada."
        )
        return None

    print(
        f"[{time.strftime('%H:%M:%S')}] Encontradas {len(tables)} tabelas de resultados."
    )

    # Processar os dados da tabela e convertê-los em um DataFrame
    print(f"[{time.strftime('%H:%M:%S')}] Processando dados das tabelas...")
    turmas_data = []

    for table_counter, table in enumerate(tables, 1):
        # Extrair cabeçalhos
        headers = []
        header_row = table.find("tr", {"class": "linhaTitulo"})
        if header_row:
            headers = [th.text.strip() for th in header_row.find_all("th")]

        rows = table.find_all("tr")
        print(
            f"[{time.strftime('%H:%M:%S')}] Processando tabela {table_counter} com {len(rows)} linhas."
        )

        # Variáveis para armazenar os detalhes do componente atual
        current_component_id = None
        current_component_details = {}
        current_component_name = ""

        # Processar as linhas da tabela
        for row in rows:
            # Verificar se é uma linha de agrupador (contém o link para o componente)
            if "agrupador" in row.get("class", []):
                # Buscar o link que contém o ID do componente
                link = row.find("a")
                if link:
                    # Extrair o ID do componente do atributo onclick
                    onclick = link.get("onclick", "")
                    id_match = re.search(r"'id':'(\d+)'", onclick)

                    if id_match:
                        # Atualizar o ID do componente atual
                        current_component_id = id_match.group(1)

                        # Extrair o nome do componente
                        title_span = link.find("span", {"class": "tituloDisciplina"})
                        if title_span:
                            current_component_name = title_span.text.strip()

                        print(
                            f"[{time.strftime('%H:%M:%S')}] Encontrado componente: {current_component_name} (ID: {current_component_id})"
                        )

                        # Adicionar um pequeno delay para não sobrecarregar o servidor
                        time.sleep(1)

                        # Obter detalhes do componente
                        current_component_details = coleta_dados(
                            session, current_component_id, viewstate, base_url, debug
                        )
                    else:
                        print(
                            f"[{time.strftime('%H:%M:%S')}] AVISO: Não foi possível extrair o ID do componente do onclick: {onclick}"
                        )
                        current_component_id = None
                        current_component_details = {}

            # Para as linhas de dados (não agrupador e não cabeçalho)
            elif "linhaTitulo" not in row.get(
                "class", []
            ) and "agrupador" not in row.get("class", []):
                cols = row.find_all("td")

                if len(cols) >= 5:  # Verificar se a linha tem colunas suficientes
                    try:
                        # Extrair informações da turma
                        turma_info = {
                            "codigo": cols[0].text.strip(),
                            "disciplina": current_component_name
                            or cols[1].text.strip(),
                            "turma": cols[2].text.strip(),
                            "horario": cols[3].text.strip(),
                            "local": cols[4].text.strip(),
                            "docente": (
                                cols[5].text.strip()
                                if len(cols) > 5
                                else "Não informado"
                            ),
                        }

                        # Adicionar os detalhes do componente se disponíveis
                        if current_component_details:
                            turma_info.update(current_component_details)

                        turmas_data.append(turma_info)
                    except Exception as e:
                        print(
                            f"[{time.strftime('%H:%M:%S')}] ERRO ao processar uma linha: {str(e)}"
                        )

    if not turmas_data:
        print(
            f"[{time.strftime('%H:%M:%S')}] ERRO: Nenhum dado encontrado nas tabelas."
        )
        return None

    # Criar DataFrame com os resultados
    df_turmas = pd.DataFrame(turmas_data)

    print(
        f"[{time.strftime('%H:%M:%S')}] Extração concluída. Foram encontradas {len(df_turmas)} turmas."
    )

    # Criar pasta de dados se não existir
    data_dir = "dados"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Salvar em CSV
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    csv_filename = os.path.join(data_dir, f"turmas_unb_gama_{timestamp}.csv")
    print(f"[{time.strftime('%H:%M:%S')}] Salvando dados em: {csv_filename}")

    try:
        df_turmas.to_csv(csv_filename, index=False, encoding="utf-8-sig")
        print(f"[{time.strftime('%H:%M:%S')}] Dados salvos com sucesso.")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ERRO ao salvar CSV: {str(e)}")

    print(f"[{time.strftime('%H:%M:%S')}] ====== PROCESSO CONCLUÍDO COM SUCESSO ======")
    return df_turmas


if __name__ == "__main__":
    try:
        # Por padrão, executar sem debug
        debug_mode = False

        # Verificar se há argumentos de linha de comando
        import sys

        if len(sys.argv) > 1 and sys.argv[1].lower() == "--debug":
            debug_mode = True
            print(
                f"[{time.strftime('%H:%M:%S')}] Modo de depuração ativado. Os arquivos HTML serão salvos."
            )

        resultado = scrape_unb_classes(debug=debug_mode)
        if resultado is not None:
            print(
                f"[{time.strftime('%H:%M:%S')}] Primeiras linhas dos dados extraídos:"
            )
            print(resultado.head())
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Nenhum resultado foi retornado.")
    except Exception as e:
        print(
            f"[{time.strftime('%H:%M:%S')}] ERRO CRÍTICO durante o scraping: {str(e)}"
        )
        import traceback

        traceback.print_exc()
