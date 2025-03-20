import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import os
import re
from dotenv import load_dotenv
from bedrock_agent import BedrockAgentClient

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="Sistema UnB - Cursos e Recomendação de Disciplinas",
    page_icon="🎓",
    layout="wide"
)

# Verificação de variáveis de ambiente AWS para Bedrock
required_vars = ['AWS_DEFAULT_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    st.error(f"Faltam as seguintes variáveis de ambiente: {', '.join(missing_vars)}")
    st.stop()

# Função para extrair disciplinas da resposta
def extract_disciplinas(text):
    disciplinas = []
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if re.match(r'^[\d\-\*\•]+\.?\s+', line):
            disciplina_name = re.sub(r'^[\d\-\*\•]+\.?\s+', '', line)
            disciplina_name = re.sub(r'^[A-Z]{3}\d{4}\s*[\-:]\s*', '', disciplina_name)
            disciplinas.append(disciplina_name)
    if not disciplinas:
        disciplinas = re.findall(r'["\']([^"\']+)["\']|["\[\(]([^\]\)]+)[\]\)]', text)
        disciplinas = [d[0] if d[0] else d[1] for d in disciplinas]
    return disciplinas

# Função para instruções de alias no Bedrock Agent
def create_alias_instructions():
    st.error("Seu agente não possui um alias. É necessário criar um alias antes de poder usar o agente.")
    st.markdown("""
    ### Como criar um alias para seu agente:
    1. Acesse o [console AWS Bedrock](https://console.aws.amazon.com/bedrock)
    2. No menu lateral, clique em "Agentes"
    3. Selecione seu agente "grade-agent"
    4. Clique no botão "Criar alias" no topo da página
    5. Defina um nome para o alias (ex: "prod")
    6. Selecione a versão mais recente do agente
    7. Clique em "Criar"
    8. Copie o ID do alias criado e adicione no .env (BEDROCK_AGENT_ALIAS_ID)
    """)
    st.info("Após criar o alias, reinicie esta aplicação.")

# Tabs para funcionalidades
tabs = st.tabs(["📍 Dashboard de Cursos", "📚 Recomendação de Disciplinas"])

# =======================
# TAB 1 - DASHBOARD DE CURSOS
# =======================
with tabs[0]:
    st.header("📍 Dashboard de Cursos e Localização dos Campi")

    file_path = os.path.join('dados', 'cursos-de-graduacao.json')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            cursos_json = json.load(f)

        campus_coords = {
            "DARCY RIBEIRO": {"latitude": -15.7634, "longitude": -47.8707},
            "FACULDADE DO GAMA": {"latitude": -15.9892, "longitude": -48.0546},
            "FACULDADE DE CEILÂNDIA": {"latitude": -15.8303,    "longitude": -48.1002},
            "FACULDADE DE PLANALTINA":{ "latitude": -15.6100,  "longitude": -47.6500}
        }

        df_cursos = pd.DataFrame(cursos_json)

        curso_nome = st.selectbox('Selecione um curso:', df_cursos['nome'].unique())

        curso_selecionado = df_cursos[df_cursos['nome'] == curso_nome].iloc[0]

        campus_nome = curso_selecionado['campus']
        coords = campus_coords.get(campus_nome, {"latitude": 0.0, "longitude": 0.0})

        st.subheader(f"Informações do Curso: {curso_nome}")
        st.write(f"Campus: {campus_nome}")
        st.write(f"Coordenador: {curso_selecionado['coordenador']}")

        st.subheader("Localização no Mapa:")

        df_mapa = pd.DataFrame([{
            'latitude': coords['latitude'],
            'longitude': coords['longitude']
        }])

        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/streets-v12',
            initial_view_state=pdk.ViewState(
                latitude=coords['latitude'],
                longitude=coords['longitude'],
                zoom=12,
                pitch=50,
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=df_mapa,
                    get_position='[longitude, latitude]',
                    get_color='[200, 30, 0, 160]',
                    get_radius=500,
                ),
            ],
        ))

    except FileNotFoundError:
        st.error(f"Arquivo não encontrado no caminho: {file_path}")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")

# ==============================  
# TAB 2 - RECOMENDAÇÃO DE DISCIPLINAS  
# ==============================
with tabs[1]:
    st.header("📚 Sistema de Recomendação de Disciplinas - UnB")
    st.markdown("""
    Este sistema utiliza inteligência artificial para recomendar disciplinas 
    baseadas no seu curso e área de interesse.
    """)

    st.sidebar.header("Informações do Estudante")

    # Carregar lista de cursos do JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            cursos_json = json.load(f)

        df_cursos_sidebar = pd.DataFrame(cursos_json)
        cursos_lista = sorted(df_cursos_sidebar['nome'].unique().tolist())
        cursos_lista.append("Outro (especifique abaixo)")

    except Exception as e:
        st.error(f"Erro ao carregar cursos para recomendação: {str(e)}")
        cursos_lista = ["Outro (especifique abaixo)"]

    curso_selecionado = st.sidebar.selectbox("Selecione seu curso:", cursos_lista)

    if curso_selecionado == "Outro (especifique abaixo)":
        curso_personalizado = st.sidebar.text_input("Digite o nome do seu curso:")
        curso = curso_personalizado if curso_personalizado else "Não especificado"
    else:
        curso = curso_selecionado

    area_interesse = st.sidebar.text_input("Digite sua área de interesse:")

    # (segue o restante do código normalmente...)

    # Session states
    if 'recommendations_result' not in st.session_state:
        st.session_state.recommendations_result = None

    if 'disciplinas_list' not in st.session_state:
        st.session_state.disciplinas_list = []

    if 'disciplina_description' not in st.session_state:
        st.session_state.disciplina_description = None

    if st.sidebar.button("Obter Recomendações"):
        if not curso or not area_interesse:
            st.error("Por favor, preencha todos os campos antes de continuar.")
        else:
            with st.spinner("Consultando o sistema de recomendações..."):
                try:
                    bedrock_client = BedrockAgentClient()
                    resultado = bedrock_client.get_recommendations(curso, area_interesse)
                    st.session_state.recommendations_result = resultado

                    if resultado['success']:
                        disciplinas = extract_disciplinas(resultado['recommendations'])
                        st.session_state.disciplinas_list = disciplinas
                        st.session_state.disciplina_description = None
                except Exception as e:
                    st.error(f"Ocorreu um erro inesperado: {str(e)}")
                    st.info("Verifique se todas as variáveis de ambiente da AWS estão configuradas corretamente.")

    if st.session_state.recommendations_result and st.session_state.recommendations_result['success']:
        resultado = st.session_state.recommendations_result
        st.success("Recomendações obtidas com sucesso!")
        st.markdown(f"**Curso:** {curso}")
        st.markdown(f"**Área de Interesse:** {area_interesse}")
        st.markdown("### Disciplinas Recomendadas")
        st.markdown(resultado['recommendations'])

        if st.session_state.disciplinas_list:
            st.subheader("Obter mais informações sobre uma disciplina")
            selected_disciplina = st.selectbox(
                "Selecione uma disciplina para saber mais:",
                [""] + st.session_state.disciplinas_list
            )

            if selected_disciplina:
                if st.button(f"Ver detalhes de '{selected_disciplina}'"):
                    with st.spinner(f"Obtendo informações sobre {selected_disciplina}..."):
                        try:
                            bedrock_client = BedrockAgentClient()
                            desc_resultado = bedrock_client.disciplina_description(selected_disciplina)
                            st.session_state.disciplina_description = desc_resultado
                        except Exception as e:
                            st.error(f"Ocorreu um erro ao obter detalhes: {str(e)}")

            if st.session_state.disciplina_description and st.session_state.disciplina_description['success']:
                st.subheader(f"Sobre a disciplina: {selected_disciplina}")
                st.markdown(st.session_state.disciplina_description['description'])

        st.info("""
        **Nota:** Estas recomendações são geradas por IA e devem ser verificadas no sistema oficial da UnB.
        """)

    else:
        st.info("""
        👈 Preencha os dados no painel lateral e clique em "Obter Recomendações".
        """)

        st.markdown("### Exemplos de uso")
        st.markdown("""
        - **Exemplo 1:** Curso de Ciência da Computação com interesse em IA
        - **Exemplo 2:** Curso de Engenharia Mecânica com interesse em Energias Renováveis
        """)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Sobre o Sistema")
    st.sidebar.info("""
    Sistema utilizando AWS Bedrock para fornecer recomendações
    personalizadas de disciplinas.
    """)