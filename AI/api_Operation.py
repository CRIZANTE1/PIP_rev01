# FILE: AI/api_Operation.py

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
        # Seu modelo original para todas as operações
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

    #----------------- Função para fazer perguntas ao modelo Gemini (sua versão original) ----------------------
    def ask_gemini(self, pdf_files, question):
        try:
            progress_bar = st.progress(0)
            
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
            progress_bar.progress(60)
            
            # Usa o seu modelo principal
            response = self.model.generate_content(inputs)
            progress_bar.progress(100)
            st.success("Resposta gerada com sucesso!")
            return response.text
            
        except Exception as e:
            st.error(f"Erro ao obter resposta do modelo Gemini: {str(e)}")
            return None

    #----------------- Função para limpar a resposta JSON (segurança) ----------------------
    def _clean_json_string(self, text):
        """Limpa o texto da resposta da IA para extrair apenas o JSON."""
        match = re.search(r'```(json)?\s*({.*?})\s*```', text, re.DOTALL)
        if match:
            return match.group(2)
        return text.strip()

    #----------------- NOVA FUNÇÃO: Extração de Dados Estruturados ----------------------
    def extract_structured_data(self, pdf_file, prompt):
        """
        Extrai dados estruturados de um ÚNICO PDF, solicitando uma resposta em JSON.
        """
        if not pdf_file:
            st.warning("Nenhum arquivo PDF fornecido para extração.")
            return None

        try:
            with st.spinner(f"Analisando '{pdf_file.name}' com IA para extrair dados..."):
                pdf_bytes = pdf_file.read()
                pdf_file.seek(0)

                part_pdf = {"mime_type": "application/pdf", "data": pdf_bytes}
                
                # Configuração para solicitar JSON
                generation_config = genai.types.GenerationConfig(response_mime_type="application/json")

                # Usa o seu modelo principal com a configuração de resposta JSON
                response = self.model.generate_content(
                    [prompt, part_pdf],
                    generation_config=generation_config
                )
                
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
            st.exception(e) # Para mais detalhes no log
            return None

    #----------------- Função principal para responder perguntas (sua versão original) ---------------
    def answer_question(self, pdf_files, question):
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




   






   





   




   



