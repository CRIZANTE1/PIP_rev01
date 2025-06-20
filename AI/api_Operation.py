import google.generativeai as genai
from google.generativeai.types import content_types
from AI.api_load import load_api
import time
import numpy as np
import streamlit as st
import re
import pandas as pd
import json


class PDFQA:
    def __init__(self):
        load_api()  # Carrega a API
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')


   
    #----------------- Função para fazer perguntas ao modelo Gemini----------------------
    def ask_gemini(self, pdf_files, question):
        """
        (Funcionalidade Original) Envia múltiplos PDFs e uma pergunta de texto para o modelo de QA.
        Retorna a resposta como uma string de texto.
        """
        try:
            progress_bar = st.progress(0, text="Analisando documentos para responder à pergunta...")
            
            inputs = []
            progress_bar.progress(20)
            
            for pdf_file in pdf_files:
                if hasattr(pdf_file, 'read'):
                    pdf_bytes = pdf_file.read()
                    pdf_file.seek(0)  
                else:
                    with open(pdf_file, 'rb') as f:
                        pdf_bytes = f.read()
                
                part = {"mime_type": "application/pdf", "data": pdf_bytes}
                inputs.append(part)
            
            progress_bar.progress(40)
            
            inputs.append({"text": question})
            
            progress_bar.progress(60, text="Gerando resposta com a IA...")
            response = self.qa_model.generate_content(inputs)
            progress_bar.progress(100, text="Resposta recebida!")
            st.success("Resposta gerada com sucesso!")
            
            return response.text
            
        except Exception as e:
            st.error(f"Erro ao obter resposta do modelo Gemini: {str(e)}")
            return None

    def _clean_json_string(self, text):
        """
        Função de segurança para limpar a resposta da IA e extrair um bloco JSON.
        Útil caso a API não retorne JSON puro.
        """
        match = re.search(r'```(json)?\s*({.*?})\s*```', text, re.DOTALL)
        if match:
            return match.group(2)
        return text.strip()

    def extract_structured_data(self, pdf_file, prompt):
        """
        (Nova Funcionalidade) Extrai dados estruturados de um ÚNICO PDF.
        Usa um prompt específico e o modelo otimizado para retornar um dicionário Python.
        
        Args:
            pdf_file: Um objeto de arquivo PDF (ex: st.UploadedFile).
            prompt (str): A instrução para a IA sobre quais dados extrair.
            
        Returns:
            dict: Um dicionário com os dados extraídos ou None em caso de erro.
        """
        if not pdf_file:
            st.warning("Nenhum arquivo PDF fornecido para extração.")
            return None

        try:
            with st.spinner(f"Analisando '{pdf_file.name}' com IA para extrair dados..."):
                pdf_bytes = pdf_file.read()
                pdf_file.seek(0)  # Reseta o ponteiro do arquivo para reutilização

                part_pdf = {"mime_type": "application/pdf", "data": pdf_bytes}

                # Usa o modelo de extração com o prompt
                response = self.extraction_model.generate_content([prompt, part_pdf])
                
                # A API com response_mime_type="application/json" já deve retornar JSON puro.
                # A limpeza é uma camada extra de segurança.
                cleaned_response = self._clean_json_string(response.text)
                extracted_data = json.loads(cleaned_response)
                
                st.success(f"Dados extraídos com sucesso de '{pdf_file.name}'!")
                return extracted_data
                
        except json.JSONDecodeError:
            st.error("Erro na extração: A IA não retornou um JSON válido. Verifique o documento ou tente novamente.")
            st.text_area("Resposta recebida da IA (para depuração):", value=response.text, height=150)
            return None
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o PDF com a IA: {e}")
            return None
            
    def answer_question(self, pdf_files, question):
        """
        (Funcionalidade Original) Wrapper para o método ask_gemini, medindo o tempo de resposta.
        """
        start_time = time.time()
        try:
            answer = self.ask_gemini(pdf_files, question)
            if answer:
                return answer, time.time() - start_time
            else:
                st.error("Não foi possível obter uma resposta do modelo.")
                return None, 0
        except Exception as e:
            st.error(f"Erro inesperado ao processar a pergunta: {str(e)}")
            st.exception(e)
            return None, 0





   






   





   




   



