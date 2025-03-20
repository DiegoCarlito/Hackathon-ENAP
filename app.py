import streamlit as st
import os
from dotenv import load_dotenv
from bedrock_agent import BedrockAgentClient
import re

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="Recomendação de Disciplinas - UnB",
    page_icon="📚",
    layout="wide"
)

# Função para extrair disciplinas da resposta
def extract_disciplinas(text):
    # Esta função extrai os nomes das disciplinas do texto retornado pelo agente
    # Aqui estamos supondo que as disciplinas estão listadas em formato de lista
    # com números, pontos ou traços. Ajuste conforme necessário de acordo com o formato real.
    disciplinas = []
    
    # Procurar por padrões como "1. Nome da Disciplina" ou "- Nome da Disciplina"
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        # Verificar se a linha parece ser uma disciplina (começa com número ou traço)
        if re.match(r'^[\d\-\*\•]+\.?\s+', line):
            # Extrair o nome da disciplina removendo o prefixo
            disciplina_name = re.sub(r'^[\d\-\*\•]+\.?\s+', '', line)
            # Também remover qualquer código de disciplina no início (ex: "CIC1234 - ")
            disciplina_name = re.sub(r'^[A-Z]{3}\d{4}\s*[\-:]\s*', '', disciplina_name)
            disciplinas.append(disciplina_name)
    
    # Se não encontrar nada com o padrão acima, tente outro enfoque
    if not disciplinas:
        # Procurar por disciplinas destacadas em aspas ou entre colchetes
        disciplinas = re.findall(r'["\']([^"\']+)["\']|["\[\(]([^\]\)]+)[\]\)]', text)
        # Achatando a lista resultante
        disciplinas = [d[0] if d[0] else d[1] for d in disciplinas]
    
    return disciplinas

# Título e descrição
st.title("📚 Sistema de Recomendação de Disciplinas - UnB")
st.markdown("""
Este sistema utiliza inteligência artificial para recomendar disciplinas 
baseadas no seu curso e área de interesse. As recomendações são personalizadas
através de um agente da AWS que acessa a Base de Conhecimento das disciplinas da UnB.
""")

# Sidebar para entrada de dados
st.sidebar.header("Informações do Estudante")

# Adicionando alguns cursos da UnB como exemplos
cursos = [
    "Ciência da Computação",
    "Engenharia de Software",
    "Engenharia Mecânica",
    "Medicina",
    "Direito",
    "Psicologia",
    "Administração",
    "Outro (especifique abaixo)"
]

# Seleção do curso
curso_selecionado = st.sidebar.selectbox("Selecione seu curso:", cursos)

# Campo adicional caso o curso seja "Outro"
if curso_selecionado == "Outro (especifique abaixo)":
    curso_personalizado = st.sidebar.text_input("Digite o nome do seu curso:")
    curso = curso_personalizado if curso_personalizado else "Não especificado"
else:
    curso = curso_selecionado

# Área de interesse
area_interesse = st.sidebar.text_input("Digite sua área de interesse:")

# Inicializar session_state para armazenar o resultado
if 'recommendations_result' not in st.session_state:
    st.session_state.recommendations_result = None

if 'disciplinas_list' not in st.session_state:
    st.session_state.disciplinas_list = []

if 'disciplina_description' not in st.session_state:
    st.session_state.disciplina_description = None

# Botão para obter recomendações
if st.sidebar.button("Obter Recomendações"):
    if not curso or not area_interesse:
        st.error("Por favor, preencha todos os campos antes de continuar.")
    else:
        with st.spinner("Consultando o sistema de recomendações..."):
            try:
                # Instanciar o cliente do Bedrock Agent
                bedrock_client = BedrockAgentClient()
                
                # Obter recomendações
                resultado = bedrock_client.get_recommendations(curso, area_interesse)
                
                # Armazenar o resultado no session_state
                st.session_state.recommendations_result = resultado
                
                # Extrair lista de disciplinas se houver recomendações
                if resultado['success']:
                    disciplinas = extract_disciplinas(resultado['recommendations'])
                    st.session_state.disciplinas_list = disciplinas
                    st.session_state.disciplina_description = None  # Limpar descrição anterior
                
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado: {str(e)}")
                st.info("Verifique se todas as variáveis de ambiente da AWS estão configuradas corretamente.")

# Se houver recomendações, exibi-las
if st.session_state.recommendations_result and st.session_state.recommendations_result['success']:
    resultado = st.session_state.recommendations_result
    
    st.success("Recomendações obtidas com sucesso!")
    
    # Container principal para as recomendações
    with st.container():
        st.subheader("Recomendações de Disciplinas")
        st.markdown(f"**Curso:** {curso}")
        st.markdown(f"**Área de Interesse:** {area_interesse}")
        
        # Exibir as recomendações em um bloco destacado
        st.markdown("### Disciplinas Recomendadas")
        st.markdown(resultado['recommendations'])
        
        # Select box para escolher uma disciplina e ver mais detalhes
        if st.session_state.disciplinas_list:
            st.subheader("Obter mais informações sobre uma disciplina")
            selected_disciplina = st.selectbox(
                "Selecione uma disciplina para saber mais:",
                [""] + st.session_state.disciplinas_list
            )
            
            if selected_disciplina:
                # Botão para obter detalhes da disciplina
                if st.button(f"Ver detalhes de '{selected_disciplina}'"):
                    with st.spinner(f"Obtendo informações sobre {selected_disciplina}..."):
                        try:
                            # Instanciar o cliente do Bedrock Agent (ou usar o existente)
                            bedrock_client = BedrockAgentClient()
                            
                            # Obter descrição da disciplina
                            desc_resultado = bedrock_client.disciplina_description(selected_disciplina)
                            
                            # Armazenar o resultado no session_state
                            st.session_state.disciplina_description = desc_resultado
                            
                        except Exception as e:
                            st.error(f"Ocorreu um erro ao obter detalhes: {str(e)}")
            
            # Se houver uma descrição disponível, exibi-la
            if st.session_state.disciplina_description and st.session_state.disciplina_description['success']:
                st.subheader(f"Sobre a disciplina: {selected_disciplina}")
                st.markdown(st.session_state.disciplina_description['description'])
        
        # Nota sobre as recomendações
        st.info("""
        **Nota:** Estas recomendações são geradas por um sistema de IA e devem ser consideradas como 
        sugestões. Sempre consulte o coordenador do seu curso ou o sistema oficial da UnB para 
        confirmar a disponibilidade e adequação das disciplinas ao seu currículo.
        """)

# Informações adicionais no rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("### Sobre o Sistema")
st.sidebar.info("""
Este sistema utiliza o Amazon Bedrock para fornecer recomendações
personalizadas de disciplinas baseadas na Base de Conhecimento da UnB.
""")

# Área principal - instruções iniciais (mostradas apenas quando não há resultado)
if 'recommendations_result' not in st.session_state or st.session_state.recommendations_result is None:
    with st.container():
        st.info("""
        👈 Para começar, preencha as informações no painel lateral e clique em "Obter Recomendações".
        
        O sistema analisará seu perfil e fornecerá sugestões de disciplinas que podem
        ser interessantes para sua formação acadêmica.
        """)
        
        # Exemplos de como usar
        st.markdown("### Exemplos de uso")
        st.markdown("""
        - **Exemplo 1:** Curso de Ciência da Computação com interesse em Inteligência Artificial
        - **Exemplo 2:** Curso de Engenharia Mecânica com interesse em Energia Renovável
        - **Exemplo 3:** Curso de Psicologia com interesse em Neurociência
        """)

# Adicione esta função após a definição do layout principal e antes da verificação de variáveis de ambiente

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
    8. Após a criação, copie o ID do alias criado
    9. Adicione o ID copiado à variável de ambiente `BEDROCK_AGENT_ALIAS_ID` no arquivo `.env`
    """)
    
    st.info("Após criar o alias, reinicie esta aplicação para que as alterações sejam aplicadas.")

# Executar o app
if __name__ == "__main__":
    # Verificar se as variáveis de ambiente necessárias estão configuradas
    required_vars = ['AWS_DEFAULT_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        st.error(f"Faltam as seguintes variáveis de ambiente: {', '.join(missing_vars)}")
        st.stop() 