import json
import boto3
import base64
import os
import uuid
import re
import nltk
import requests
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# -- configuração do caminho dos dados do NLTK na AWS Lambda Layer
NLTK_DATA_PATH = "/opt/python/lib/python3.12/site-packages/nltk_data"
if os.path.exists(NLTK_DATA_PATH):
    nltk.data.path.append(NLTK_DATA_PATH)

# -- inicializa clientes da AWS
s3 = boto3.client("s3")
textract = boto3.client("textract")

# -- configurações do Gemini
GEMINI_API_KEY = "AIzaSyA8fvM6TWjglweIPc9PYTGubnQjLvnNNY8"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

BUCKET_NAME = "test-upload-folder"

def extract_text_from_image(bucket_name, file_key):
    """
    Extrai o texto de uma imagem usando o AWS Textract.
    Retorna o texto extraído e os tokens filtrados.
    """
    try:
        response = textract.detect_document_text(
            Document={'S3Object': {'Bucket': bucket_name, 'Name': file_key}}
        )
        extracted_text = "\n".join(item['Text'] for item in response.get('Blocks', []) if item.get('BlockType') == 'LINE')
        
        # -- filtra tokens relevantes usando NLTK
        tokens = word_tokenize(extracted_text, language='portuguese')
        stop_words = set(stopwords.words("portuguese"))
        filtered_tokens = [token for token in tokens if token.lower() not in stop_words]
        
        return extracted_text, filtered_tokens
    except Exception as e:
        print(f"Erro ao extrair texto da imagem: {str(e)}")
        raise

def extract_invoice_data(text):
    """
    Extrai os campos padronizados da nota fiscal a partir do texto.
    Retorna um dicionário com os campos identificados.
    """
    data = {
        "nome_emissor": None,
        "CNPJ_emissor": None,
        "endereco_emissor": None,
        "CNPJ_CPF_consumidor": None,
        "data_emissao": None,
        "numero_nota_fiscal": None,
        "serie_nota_fiscal": None,
        "valor_total": None,
        "forma_pgto": None
    }

    text = re.sub(r'\s+', ' ', text).strip()
    text_lower = text.lower()
    
    # -- nome do emissor
    nome_match = re.search(r'^[A-Za-zÀ-ÖØ-öø-ÿ\s]+', text)
    if nome_match:
        data["nome_emissor"] = nome_match.group(0).strip()

    # -- CNPJ do emissor
    cnpj_pattern = r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b'
    cnpj_match = re.search(cnpj_pattern, text)
    if cnpj_match:
        data["CNPJ_emissor"] = cnpj_match.group(0)

    # -- endereço do emissor
    endereco_match = re.search(r'(rua|avenida|av\.|r\.)\s+[\w\s,.-]+', text_lower, re.IGNORECASE)
    if endereco_match:
        data["endereco_emissor"] = endereco_match.group(0).strip()

    # -- CNPJ/CPF do consumidor
    cpf_pattern = r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b'
    cpf_match = re.search(cpf_pattern, text)
    if cpf_match:
        data["CNPJ_CPF_consumidor"] = cpf_match.group(0)

    # -- data de emissão
    data_match = re.search(r'\b\d{2}/\d{2}/\d{4}\b', text)
    if data_match:
        data["data_emissao"] = data_match.group(0)

    # -- número da nota fiscal
    numero_match = re.search(r'nota fiscal\s*(?:n[ºo°]?)?\s*(\d+)', text_lower, re.IGNORECASE)
    if numero_match:
        data["numero_nota_fiscal"] = numero_match.group(1)

    # -- série da nota fiscal
    serie_match = re.search(r's[eé]rie\s*(\d+)', text_lower, re.IGNORECASE)
    if serie_match:
        data["serie_nota_fiscal"] = serie_match.group(1)

    # -- valor total
    valor_match = re.search(r'valor total[:\s]r?\$?\s([\d\.,]+)', text_lower, re.IGNORECASE)
    if valor_match:
        valor = valor_match.group(1).replace(".", "").replace(",", ".")
        data["valor_total"] = f"{float(valor):.2f}"

    # -- forma de pagamento
    if "dinheiro" in text_lower:
        data["forma_pgto"] = "dinheiro"
    elif "pix" in text_lower:
        data["forma_pgto"] = "pix"
    elif "cartão" in text_lower or "credito" in text_lower or "debito" in text_lower:
        data["forma_pgto"] = "cartão"
    elif "transferência" in text_lower or "ted" in text_lower:
        data["forma_pgto"] = "transferência"
    else:
        data["forma_pgto"] = "outros"

    return data

def refine_data_with_gemini(extracted_text):
    """
    Refina os dados extraídos usando a API do Gemini.
    Retorna um dicionário com os campos refinados.
    """
    prompt = f"""
    Você é um sistema avançado de processamento de documentos fiscais. Sua tarefa é analisar o texto de uma nota fiscal e extrair as seguintes informações:

    1. Nome completo do emissor (pessoa física ou razão social da empresa).
    2. CNPJ do emissor (para empresas) ou CPF (para pessoas físicas).
    3. Endereço completo do emissor (rua, número, bairro, cidade, estado e CEP).
    4. CNPJ ou CPF do consumidor (identificação do comprador ou destinatário).
    5. Data de emissão da nota fiscal (no formato DD/MM/AAAA).
    6. Número da nota fiscal (código único de identificação).
    7. Série da nota fiscal (número da série, se disponível).
    8. Valor total da compra (incluindo impostos, no formato XXXX.XX).
    9. Forma de pagamento utilizada (dinheiro, PIX, cartão de crédito/débito, boleto, etc.).

    Caso algum campo não seja encontrado no texto, preencha-o com "None".

    Aqui está o texto da nota fiscal para análise:
    "{extracted_text}"

    Retorne os dados extraídos no formato JSON abaixo, sem incluir comentários ou explicações adicionais:

    {{
        "nome_emissor": "<nome-do-emissor>",
        "CNPJ_emissor": "00.000.000/0000-00",
        "endereco_emissor": "<endereco-completo>",
        "CNPJ_CPF_consumidor": "000.000.000-00",
        "data_emissao": "00/00/0000",
        "numero_nota_fiscal": "123456",
        "serie_nota_fiscal": "123",
        "valor_total": "0000.00",
        "forma_pgto": "<forma-de-pagamento>"
    }}
    """

    headers = {
        "Content-Type": "application/json",
    }
    params = {
        "key": GEMINI_API_KEY,
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    llm_response = {}
    # -- envia a requisição para a API do Gemini
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload)
        response.raise_for_status() 
        response_data = response.json()

        # -- extrai o texto da resposta
        if "candidates" in response_data and response_data["candidates"]:
            text_response = response_data["candidates"][0]["content"]["parts"][0]["text"]
            refined_info = _extrair_json(text_response)

            #-- verifica se foi possível extrair o JSON da resposta
            if not isinstance(refined_info, dict):
                # -- retorna o erro
                return refined_info
            else:
                # -- retorna a resposta do llm
                return {"llm_status": "Texto refinado com sucesso usando o Gemini",
                        "status_code": 200,
                        "refined_text": refined_info}

        else:
            # -- retorna o erro caso a resposta do Gemini não contenha dados válidos
            llm_response.update({
                "llm_status": "A resposta do Gemini não contém dados válidos",
                "status_code": 500})
            return llm_response
    except Exception as e:
        # -- retorna erros ao tentar refinar o texto com o Gemini
        llm_response.update({
            "llm_status": f"Falha ao refinar o texto com o Gemini: {str(e)}",
            "status_code": 500})
        return llm_response

def _extrair_json(texto):
    """
    Extrai o JSON da resposta do Gemini.
    """
    try:
        # -- remove possíveis marcações ou comentários
        inicio = texto.find("{")
        fim = texto.rfind("}")
        if inicio == -1 or fim == -1:
            raise ValueError("JSON não encontrado no texto.")
        json_str = texto[inicio:fim + 1]
        return json.loads(json_str)
    except Exception as e:
        # -- retorna um erro caso não seja possível extrair o JSON
        return {
            "llm_status": f"Falha ao extrair o JSON: {str(e)}",
            "status_code": 500
        }

def validate_extracted_data(invoice_data):
    """
    Valida os dados extraídos e corrige campos incompletos ou inválidos.
    """
    # -- exemplo: Corrigir o nome do emissor se estiver incompleto
    if invoice_data["nome_emissor"] and len(invoice_data["nome_emissor"].split()) < 2:
        invoice_data["nome_emissor"] = None  

    # -- exemplo: Corrigir o CNPJ/CPF se estiver mal formatado
    cnpj_pattern = r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b'
    cpf_pattern = r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b'
    
    if invoice_data["CNPJ_emissor"] and not re.match(cnpj_pattern, invoice_data["CNPJ_emissor"]):
        invoice_data["CNPJ_emissor"] = None

    if invoice_data["CNPJ_CPF_consumidor"] and not re.match(cpf_pattern, invoice_data["CNPJ_CPF_consumidor"]):
        invoice_data["CNPJ_CPF_consumidor"] = None

    return invoice_data

def lambda_handler(event, context):
    """
    Função principal da Lambda. Recebe um arquivo de imagem,
    processa com Textract e retorna os dados extraídos.
    """
    try:
        print("Lambda foi acionada com sucesso!")

        # -- verifica se o corpo da requisição está em base64 ou binário
        if event.get("isBase64Encoded", False):
            file_content = base64.b64decode(event["body"])
        else:
            file_content = event["body"].encode("utf-8")

        # -- gera um nome único para o arquivo
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}.jpeg"

        # -- faz o upload da imagem para o S3
        s3.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=file_content, ContentType="image/jpeg")
        print(f"Arquivo {file_name} salvo no bucket S3 {BUCKET_NAME}")

        # -- extrai e processa o texto da imagem
        extracted_text, filtered_tokens = extract_text_from_image(BUCKET_NAME, file_name)
        print(f"Texto extraído: {extracted_text}")
        print(f"Tokens filtrados: {filtered_tokens}")

        # -- extrai os dados da nota fiscal
        invoice_data = extract_invoice_data(extracted_text)

        # -- refina os dados com o Gemini
        refined_data = refine_data_with_gemini(extracted_text)
        if refined_data:
            for field, value in refined_data.items():
                if value:
                    invoice_data[field] = value

        # -- valida e corrige os dados extraídos
        validated_data = validate_extracted_data(invoice_data)

        # -- determina o diretório de destino com base na forma de pagamento
        if "dinheiro" in filtered_tokens or "pix" in filtered_tokens:
            destination_folder = "dinheiro/"
        else:
            destination_folder = "outros/"

        # -- novo caminho do arquivo dentro do bucket
        new_key = f"{destination_folder}{file_name}"

        # -- copia a imagem para a nova pasta no S3
        s3.copy_object(
            Bucket=BUCKET_NAME,
            CopySource={'Bucket': BUCKET_NAME, 'Key': file_name},
            Key=new_key
        )

        # -- remove o arquivo original após a cópia bem-sucedida
        s3.delete_object(Bucket=BUCKET_NAME, Key=file_name)
        print(f"Imagem movida para {new_key}")

        # -- retorna apenas o conteúdo de refined_text
        if "refined_text" in validated_data:
            return {
                'statusCode': 200,
                'body': json.dumps(validated_data["refined_text"], ensure_ascii=False, indent=4)
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps(validated_data, ensure_ascii=False, indent=4)
            }
    except Exception as e:
        print(f"Erro ao processar a solicitação: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                "error": "Erro ao processar a solicitação",
                "details": str(e)
            }, ensure_ascii=False, indent=4)
        }
