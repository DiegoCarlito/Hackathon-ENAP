import requests
from bs4 import BeautifulSoup
import json
import time
import re

def get_discipline_details(session, url, discipline_id):
    """
    Busca detalhes de uma disciplina a partir de seu ID.
    
    Args:
        session: Sessão HTTP ativa
        url: URL base do SIGAA
        discipline_id: ID da disciplina
    
    Returns:
        Dicionário com detalhes da disciplina (ementa e pré-requisitos)
    """
    # URL base é a página de componentes
    base_url = "https://sigaa.unb.br/sigaa/public/componentes/busca_componentes.jsf"
    
    # Obter a página atual para extrair o ViewState
    response = session.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    view_state = soup.find('input', {'name': 'javax.faces.ViewState'})['value']
    
    # Parâmetros para a requisição POST que simula o clique no link de detalhes
    data = {
        'formListagemComponentes': 'formListagemComponentes',
        'formListagemComponentes:j_id_jsp_190531263_23': 'formListagemComponentes:j_id_jsp_190531263_23',
        'id': discipline_id,
        'publico': 'public',
        'javax.faces.ViewState': view_state
    }
    
    # Fazer o POST para acessar os detalhes da disciplina
    response = session.post(base_url, data=data)
    
    if response.status_code != 200:
        print(f"Erro ao acessar detalhes da disciplina ID {discipline_id}: {response.status_code}")
        return None
    
    # Analisar a página de detalhes
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Inicializar dicionário para armazenar os detalhes
    details = {
        'ementa': '',
        'pre_requisitos': ''
    }
    
    # Buscar a ementa
    ementa_row = soup.find('th', text=lambda t: t and 'Ementa/Descrição' in t)
    if ementa_row:
        ementa_text = ementa_row.find_next('td').text.strip()
        details['ementa'] = ementa_text
    
    # Buscar os pré-requisitos
    prereq_row = soup.find('th', text=lambda t: t and 'Pré-Requisitos' in t)
    if prereq_row:
        prereq_text = prereq_row.find_next('td').text.strip()
        if prereq_text and prereq_text != '-':
            details['pre_requisitos'] = prereq_text
    
    return details

def get_all_disciplines():
    url = "https://sigaa.unb.br/sigaa/public/componentes/busca_componentes.jsf"
    
    # Lista para armazenar todas as disciplinas
    all_disciplines = []
    
    # Obter a página inicial para extrair o ViewState
    session = requests.Session()
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extrair o ViewState do formulário - necessário para o POST
    view_state = soup.find('input', {'name': 'javax.faces.ViewState'})['value']
    
    # Para cada unidade acadêmica
    unidades = soup.select('#form\\:unidades option')
    
    # Remover a opção "-- SELECIONE UMA UNIDADE ACADÊMICA --"
    unidades = [u for u in unidades if u['value'] != '0']
    
    # Para testes, usar apenas algumas unidades
    # unidades = unidades[:2]
    
    for unidade in unidades:
        unidade_id = unidade['value']
        unidade_nome = unidade.text
        
        print(f"Buscando disciplinas de: {unidade_nome}")
        
        # Parâmetros para a requisição POST
        data = {
            'form': 'form',
            'form:nivel': 'G',  # GRADUAÇÃO
            'form:checkTipo': 'on',
            'form:tipo': '2',   # DISCIPLINA
            'form:checkUnidade': 'on',
            'form:unidades': unidade_id,
            'form:btnBuscarComponentes': 'Buscar Componentes',
            'javax.faces.ViewState': view_state
        }
        
        # Fazer o POST
        response = session.post(url, data=data)
        result_soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extrair o novo ViewState após busca (pode mudar)
        new_view_state = result_soup.find('input', {'name': 'javax.faces.ViewState'})['value']
        
        # Extrair as disciplinas da página de resultados
        rows = result_soup.select('tr.linhaPar, tr.linhaImpar')
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:  # Verificar se tem colunas suficientes
                
                # Extrair ID da disciplina do onclick
                discipline_id = None
                link_element = cols[4].find('a', title='Detalhes do Componente Curricular')
                
                if link_element and 'onclick' in link_element.attrs:
                    onclick = link_element['onclick']
                    id_match = re.search(r"'id':'(\d+)'", onclick)
                    if id_match:
                        discipline_id = id_match.group(1)
                
                disciplina = {
                    "codigo": cols[0].text.strip(),
                    "nome": cols[1].text.strip(),
                    "tipo": cols[2].text.strip(),
                    "ch_total": cols[3].text.strip(),
                    "unidade": unidade_nome,
                    "id": discipline_id
                }
                
                # Se encontrou o ID, buscar detalhes adicionais
                if discipline_id:
                    print(f"  Obtendo detalhes de: {disciplina['codigo']} - {disciplina['nome']}")
                    
                    # Buscar detalhes da disciplina
                    details = get_discipline_details(session, url, discipline_id)
                    
                    if details:
                        disciplina.update(details)
                        
                        # Imprimir detalhes para debug
                        print(f"    Ementa: {details['ementa'][:30]}..." if details['ementa'] else "    Ementa: Não encontrada")
                        print(f"    Pré-req: {details['pre_requisitos'][:30]}..." if details['pre_requisitos'] else "    Pré-req: Não encontrado")
                    else:
                        print("    Erro ao buscar detalhes da disciplina.")
                    
                    # Pausa para não sobrecarregar o servidor
                    time.sleep(0.5)
                
                all_disciplines.append(disciplina)
        
        # Pausa para não sobrecarregar o servidor
        time.sleep(1)
        
        # Salvamento parcial após cada unidade
        with open(f'disciplinas_unb_parcial_{unidade_id}.json', 'w', encoding='utf-8') as f:
            json.dump(all_disciplines, f, ensure_ascii=False, indent=4)
    
    return all_disciplines

def main():
    print("Iniciando scraping das disciplinas da UnB...")
    disciplines = get_all_disciplines()
    
    # Salvando em um arquivo JSON
    with open('disciplinas_unb.json', 'w', encoding='utf-8') as f:
        json.dump(disciplines, f, ensure_ascii=False, indent=4)
    
    print(f"Total de disciplinas encontradas: {len(disciplines)}")
    print("Dados salvos em 'disciplinas_unb.json'")

if __name__ == "__main__":
    main()
