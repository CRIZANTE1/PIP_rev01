import streamlit as st
import pandas as pd
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import LIFTING_SHEET_NAME, CRANE_SHEET_NAME

def show_history_page():
    st.title("Histórico de Avaliações")

    uploader = GoogleDriveUploader()

    st.subheader("Buscar Avaliação por ID")
    search_id = st.text_input("Digite o ID da Avaliação (ex: AV20240101-abcdefgh)")

    if st.button("Buscar"):
        if search_id:
            try:
                # Buscar dados de içamento
                lifting_data = uploader.get_data_from_sheet(LIFTING_SHEET_NAME)
                # Buscar dados do guindauto
                crane_data = uploader.get_data_from_sheet(CRANE_SHEET_NAME)

                # Encontrar a linha correspondente ao ID em ambos os datasets
                found_lifting = None
                if lifting_data:
                    # Assumindo que a primeira linha são os cabeçalhos
                    headers_lifting = lifting_data[0]
                    for row in lifting_data[1:]:
                        if row and row[0] == search_id: # Assumindo que o ID está na primeira coluna
                            found_lifting = dict(zip(headers_lifting, row))
                            break
                
                found_crane = None
                if crane_data:
                    # Assumindo que a primeira linha são os cabeçalhos
                    headers_crane = crane_data[0]
                    for row in crane_data[1:]:
                        if row and row[0] == search_id: # Assumindo que o ID está na primeira coluna
                            found_crane = dict(zip(headers_crane, row))
                            break

                if found_lifting or found_crane:
                    st.success(f"Avaliação encontrada para o ID: {search_id}")
                    
                    if found_lifting:
                        st.subheader("Dados de Içamento")
                        df_lifting = pd.DataFrame([found_lifting])
                        st.dataframe(df_lifting)
                    else:
                        st.info("Nenhum dado de içamento encontrado para este ID.")

                    if found_crane:
                        st.subheader("Informações do Guindauto")
                        df_crane = pd.DataFrame([found_crane])
                        st.dataframe(df_crane)
                    else:
                        st.info("Nenhuma informação de guindauto encontrada para este ID.")

                else:
                    st.warning(f"Nenhuma avaliação encontrada para o ID: {search_id}")

            except Exception as e:
                st.error(f"Erro ao buscar dados: {str(e)}")
        else:
            st.warning("Por favor, digite um ID de avaliação para buscar.")

        st.subheader("Todas as Avaliações (Dados de Içamento)")
    if st.button("Carregar Todas as Avaliações"):
        try:
            all_lifting_data = uploader.get_data_from_sheet(LIFTING_SHEET_NAME)
            if all_lifting_data:
                # Verificar e ajustar os dados antes de criar o DataFrame
                headers = all_lifting_data[0]
                data_rows = all_lifting_data[1:]
                
                # Remover colunas vazias do início
                # Encontrar a primeira coluna não vazia nos cabeçalhos
                first_valid_col = 0
                for i, header in enumerate(headers):
                    if header:  # Se o cabeçalho não estiver vazio
                        first_valid_col = i
                        break
                
                # Cortar os cabeçalhos e dados para remover colunas vazias
                headers = headers[first_valid_col:]
                normalized_data = []
                for row in data_rows:
                    if len(row) >= len(headers):
                        normalized_row = row[first_valid_col:first_valid_col + len(headers)]
                        normalized_data.append(normalized_row)
                    else:
                        # Se a linha for muito curta, preencher com None
                        normalized_row = row[first_valid_col:] + [None] * (len(headers) - len(row[first_valid_col:]))
                        normalized_data.append(normalized_row)
                
                df_all_lifting = pd.DataFrame(normalized_data, columns=headers)
                st.dataframe(df_all_lifting)
            else:
                st.info("Nenhum dado de içamento disponível.")
        except Exception as e:
            st.error(f"Erro ao carregar todas as avaliações: {str(e)}")
            # Adicionar mais informações de debug
            st.error("Detalhes do erro:")
            st.exception(e)