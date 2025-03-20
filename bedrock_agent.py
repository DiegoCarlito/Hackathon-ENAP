import boto3
import os
import json
import uuid
from typing import Dict, Any

class BedrockAgentClient:
    def __init__(self):
        """
        Inicializa o cliente do Amazon Bedrock Agent usando credenciais da AWS.
        """
        # Obtenha as credenciais da AWS das variáveis de ambiente
        region = os.environ.get('AWS_DEFAULT_REGION')
        
        # Remover aspas extras se houver 
        if region and (region.startswith('"') or region.startswith("'")):
            region = region[1:-1] if region.endswith(region[0]) else region
        
        # Inicialize o cliente do Bedrock Agents com credenciais explícitas
        self.bedrock_agent = boto3.client(
            service_name='bedrock-agent-runtime',
            region_name=region,
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.environ.get('AWS_SESSION_TOKEN')
        )
        
        # Inicializar cliente bedrock para operações de gerenciamento
        self.bedrock_management = boto3.client(
            service_name='bedrock',
            region_name=region,
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.environ.get('AWS_SESSION_TOKEN')
        )
        
        # IDs do agente e alias do agente
        self.agent_id = os.environ.get('BEDROCK_AGENT_ID')
        self.agent_alias_id = os.environ.get('BEDROCK_AGENT_ALIAS_ID')
        
        # Remover aspas extras se houver
        if self.agent_id and (self.agent_id.startswith('"') or self.agent_id.startswith("'")):
            self.agent_id = self.agent_id[1:-1] if self.agent_id.endswith(self.agent_id[0]) else self.agent_id
            
        if self.agent_alias_id and (self.agent_alias_id.startswith('"') or self.agent_alias_id.startswith("'")):
            self.agent_alias_id = self.agent_alias_id[1:-1] if self.agent_alias_id.endswith(self.agent_alias_id[0]) else self.agent_alias_id
        
        if not self.agent_id:
            raise ValueError("BEDROCK_AGENT_ID deve ser definido nas variáveis de ambiente")
            
        # Se não foi fornecido um alias, tentar buscar o "agente-alias"
        if not self.agent_alias_id:
            self.agent_alias_id = self.find_alias_by_name("agente-alias")
            
        print(f"Agent ID: {self.agent_id}")
        print(f"Agent Alias ID: {self.agent_alias_id}")

    def find_alias_by_name(self, alias_name):
        """
        Tenta encontrar um alias pelo nome
        
        Args:
            alias_name (str): Nome do alias para procurar
            
        Returns:
            str: ID do alias se encontrado, None caso contrário
        """
        try:
            # Tentar listar aliases disponíveis
            print(f"Tentando listar aliases para o agente {self.agent_id}")
            response = self.bedrock_management.list_agent_aliases(
                agentId=self.agent_id,
                maxResults=10
            )
            
            aliases = response.get('agentAliaseSummaries', [])
            
            # Procurar por um alias com o nome especificado
            for alias in aliases:
                if alias.get('agentAliasName') == alias_name:
                    alias_id = alias.get('agentAliasId')
                    print(f"Encontrado alias '{alias_name}' com ID: {alias_id}")
                    return alias_id
                    
            # Se não encontrar pelo nome específico, use o primeiro alias disponível
            if aliases:
                first_alias = aliases[0]
                alias_id = first_alias.get('agentAliasId')
                alias_name = first_alias.get('agentAliasName')
                print(f"Usando alias existente: {alias_name} (ID: {alias_id})")
                return alias_id
                
            # Nenhum alias encontrado
            print("Nenhum alias encontrado.")
            return None
                
        except Exception as e:
            print(f"Erro ao buscar aliases: {str(e)}")
            return None

    def get_recommendations(self, curso: str, area_interesse: str) -> Dict[str, Any]:
        """
        Consulta o agente do Amazon Bedrock para obter recomendações de disciplinas
        
        Args:
            curso (str): Curso do estudante
            area_interesse (str): Área de interesse do estudante
            
        Returns:
            Dict[str, Any]: Resposta do agente com recomendações
        """
        # Log para debug
        print(f"Usando agente ID: {self.agent_id}")
        print(f"Usando alias ID: {self.agent_alias_id}")
        print(f"Região: {os.environ.get('AWS_DEFAULT_REGION')}")
        
        # Verificar se temos um alias configurado
        if not self.agent_alias_id:
            return {
                'success': False,
                'error': "Alias não configurado",
                'error_details': (
                    "É necessário criar um alias para o agente chamado 'agente-alias'. "
                    "Siga as instruções na tela para criar um alias e configurar a aplicação."
                ),
                'needs_alias': True,
                'recommendations': "Não foi possível obter recomendações sem um alias configurado."
            }
        
        # Preparar a mensagem para o agente
        input_text = f"Sou estudante do curso de {curso} e tenho interesse na área de {area_interesse}. Quais disciplinas você recomenda?"
        
        try:
            # Gerar um ID de sessão único
            session_id = f"session-{uuid.uuid4().hex[:8]}"
            
            # Invocar o agente do Bedrock com o alias obrigatório
            response = self.bedrock_agent.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=input_text
            )
            
            # Processar o EventStream para extrair a resposta completa
            full_response = ""
            
            # Iterar sobre o stream de eventos para obter todas as partes da resposta
            for event in response.get('completion'):
                if 'chunk' in event:
                    # Extrair e acumular os chunks de texto
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        full_response += chunk['bytes'].decode('utf-8')
            
            # Processar e retornar a resposta
            result = {
                'success': True,
                'recommendations': full_response,
                'session_id': response.get('sessionId', '')
            }
            
            return result
            
        except Exception as e:
            # Em caso de erro, fornecer mais detalhes
            error_msg = str(e)
            
            # Mensagens de erro mais específicas
            error_details = "Não foi possível obter recomendações. "
            
            if "resourceNotFoundException" in error_msg:
                error_details += (
                    "O agente ou alias especificado não foi encontrado. "
                    "Verifique se você criou um alias chamado 'agente-alias' e "
                    "se o agente está implantado na mesma região que você está usando."
                )
                return {
                    'success': False,
                    'error': error_msg,
                    'error_details': error_details,
                    'needs_alias': True,
                    'recommendations': "Não foi possível obter recomendações."
                }
            elif "AccessDeniedException" in error_msg:
                error_details += (
                    "Suas credenciais não têm permissão para acessar este recurso. "
                    "Verifique se você tem as permissões corretas para acessar o Amazon Bedrock."
                )
            elif "badRequestException" in error_msg.lower() or "validation" in error_msg.lower() or "Missing required parameter" in error_msg:
                error_details += (
                    "Requisição inválida. É necessário criar um alias para o agente chamado 'agente-alias'. "
                    "Acesse o console da AWS e clique em 'Criar alias' para o seu agente."
                )
                return {
                    'success': False,
                    'error': error_msg,
                    'error_details': error_details,
                    'needs_alias': True,
                    'recommendations': "Não foi possível obter recomendações."
                }
            else:
                error_details += "Por favor, tente novamente mais tarde ou contate o suporte."
            
            return {
                'success': False,
                'error': error_msg,
                'error_details': error_details,
                'recommendations': "Não foi possível obter recomendações."
            }

    def disciplina_description(self, materia: str) -> Dict[str, Any]:
        """
        Consulta o agente do Amazon Bedrock para obter informações detalhadas sobre uma disciplina
        
        Args:
            materia (str): Nome da disciplina
            
        Returns:
            Dict[str, Any]: Resposta do agente com a descrição da disciplina
        """
        # Log para debug
        print(f"Obtendo descrição para a disciplina: {materia}")
        
        # Verificar se temos um alias configurado
        if not self.agent_alias_id:
            return {
                'success': False,
                'error': "Alias não configurado",
                'error_details': (
                    "É necessário criar um alias para o agente chamado 'agente-alias'. "
                    "Siga as instruções na tela para criar um alias e configurar a aplicação."
                ),
                'needs_alias': True,
                'description': "Não foi possível obter a descrição sem um alias configurado."
            }
        
        # Preparar a mensagem para o agente
        input_text = f"Quero mais informações a respeito da matéria {materia}, explique a importância dessa matéria para o desenvolvimento profissional na área. Consulte o agente responsável por descrever matérias de forma detalhada, a resposta deve seguir o padrão: 'A matéria {materia} é importante para o desenvolvimento profissional na área de 'area de interesse', pois...'."
        
        try:
            # Gerar um ID de sessão único
            session_id = f"session-{uuid.uuid4().hex[:8]}"
            
            # Invocar o agente do Bedrock com o alias obrigatório
            response = self.bedrock_agent.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=input_text
            )
            
            # Processar o EventStream para extrair a resposta completa
            full_response = ""
            
            # Iterar sobre o stream de eventos para obter todas as partes da resposta
            for event in response.get('completion'):
                if 'chunk' in event:
                    # Extrair e acumular os chunks de texto
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        full_response += chunk['bytes'].decode('utf-8')
            
            # Processar e retornar a resposta
            result = {
                'success': True,
                'description': full_response,
                'session_id': response.get('sessionId', '')
            }
            
            return result
            
        except Exception as e:
            # Em caso de erro, fornecer mais detalhes
            error_msg = str(e)
            
            # Mensagens de erro mais específicas
            error_details = "Não foi possível obter a descrição da disciplina. "
            
            if "resourceNotFoundException" in error_msg:
                error_details += (
                    "O agente ou alias especificado não foi encontrado. "
                    "Verifique se você criou um alias chamado 'agente-alias' e "
                    "se o agente está implantado na mesma região que você está usando."
                )
                return {
                    'success': False,
                    'error': error_msg,
                    'error_details': error_details,
                    'needs_alias': True,
                    'description': "Não foi possível obter a descrição."
                }
            elif "AccessDeniedException" in error_msg:
                error_details += (
                    "Suas credenciais não têm permissão para acessar este recurso. "
                    "Verifique se você tem as permissões corretas para acessar o Amazon Bedrock."
                )
            elif "badRequestException" in error_msg.lower() or "validation" in error_msg.lower() or "Missing required parameter" in error_msg:
                error_details += (
                    "Requisição inválida. É necessário criar um alias para o agente chamado 'agente-alias'. "
                    "Acesse o console da AWS e clique em 'Criar alias' para o seu agente."
                )
                return {
                    'success': False,
                    'error': error_msg,
                    'error_details': error_details,
                    'needs_alias': True,
                    'description': "Não foi possível obter a descrição."
                }
            else:
                error_details += "Por favor, tente novamente mais tarde ou contate o suporte."
            
            return {
                'success': False,
                'error': error_msg,
                'error_details': error_details,
                'description': "Não foi possível obter a descrição da disciplina."
            } 