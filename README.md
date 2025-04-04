# 📋 **API para Processamento de Notas Fiscais com AWS**

## 📖 **Sumário**

- [📋 Descrição](#-descrição)  
- [✨ Objetivos do Projeto](#-objetivos-do-projeto)  
- [🛠️ Tecnologias Utilizadas](#️-tecnologias-utilizadas)  
- [📊 Estrutura do Projeto](#-estrutura-do-projeto)  
- [✅ Atualizações Recentes](#-atualizações-recentes)  
- [👥 Autores](#-autores)  
- [⚠️ Dificuldades Enfrentadas](#-dificuldades-enfrentadas)  

---

## 📋 **Descrição**

Este projeto faz parte da Avaliação das Sprints 4, 5 e 6 do **Programa de Bolsas Compass UOL / AWS (Turma Dezembro/2024)**, focado na formação em **Inteligência Artificial para AWS**.  

O objetivo principal é desenvolver uma aplicação que receba imagens de notas fiscais simplificadas, armazene os arquivos no **AWS S3**, processe os dados utilizando o **Amazon Textract** e aplique técnicas de **NLP** para identificar os elementos da nota fiscal. O sistema retorna os dados formatados em JSON e organiza os arquivos com base na forma de pagamento.  

---

## ✨ **Objetivos do Projeto**

- 🚀 Criar uma **API REST** em Python para processamento de imagens de notas fiscais.  
- ☁️ Armazenar as notas fiscais em um **bucket S3**.  
- 📄 Processar as imagens utilizando **Amazon Textract** para extração de texto.  
- 📊 Aplicar técnicas de **NLP** para formatar os dados em JSON.  
- 🗂️ Organizar notas fiscais em pastas (`dinheiro`, `outros`) no bucket S3.  
- 🛠️ Gravar logs detalhados no **CloudWatch**.  

---

## 🛠️ **Tecnologias Utilizadas**

- 🐍 **Python**: Linguagem principal para desenvolvimento da API.  
- ☁️ **AWS S3**: Armazenamento dos arquivos de notas fiscais.  
- 📑 **Amazon Textract**: Extração de texto das imagens de notas fiscais.  
- 📚 **NLTK**: Técnicas de NLP para análise e organização dos dados.  
- 🖥️ **AWS Lambda**: Execução do código serverless.  
- 🖇️ **API Gateway**: Configuração da API REST.  
- 🔍 **CloudWatch**: Monitoramento e registro de logs.  
- 🌟 **LLM do Gemini**: Implementação de modelos de linguagem avançados para aprimorar a análise e compreensão dos dados textuais.

---


## 📊 **Estrutura do Projeto**

O projeto segue a seguinte estrutura de diretórios:  

```plaintext
├── assets            # Recursos adicionais, como imagens e outros arquivos
├── dataset           # Dados para treinamento e análise
│   └── NFs           # Notas fiscais armazenadas para processamento
├── lambda            # Código da função Lambda
├── README.md         # Documentação do projeto
```
---

## ⚠️ **Dificuldades Enfrentadas**

- **Implementar o NLTK**: A implementação do NLTK (Natural Language Toolkit) apresentou desafios relacionados à compatibilidade de versões e ao manuseio eficiente de dados textuais extraídos do Amazon Textract.
- **Implementar as bibliotecas externas no Lambda**: A integração de bibliotecas externas na função AWS Lambda envolveu dificuldades na configuração do ambiente de execução e na otimização do tamanho do pacote de implementação para garantir a performance e funcionalidade desejadas.

---


## 👥 **Autores**

- **Lucas José Leite Marino**
- **Marlon Porto Torres**  
- **Victor Silva Souza dos Santos**  
- **Victor José Marinho**
