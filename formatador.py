import streamlit as st
import pandas as pd
import unicodedata
import re
from io import BytesIO

# --- Configuração da Página ---
st.set_page_config(page_title="Padronizador de Nomes", layout="centered")

st.title("⚖️ Padronizador de Nomes de Juízes")
st.markdown("Faça upload da planilha para remover acentos, cedilhas e padronizar em caixa alta.")

# --- Função de Limpeza ---
def limpar_nome(texto):
    if not isinstance(texto, str):
        return ""
    # Normaliza (separa acentos)
    nfkd_form = unicodedata.normalize('NFKD', texto)
    # Remove acentos
    texto_sem_acento = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Caixa alta
    texto_upper = texto_sem_acento.upper()
    # Remove caracteres especiais (mantém apenas letras e espaços)
    texto_limpo = re.sub(r'[^A-Z\s]', '', texto_upper)
    # Remove espaços duplos
    return " ".join(texto_limpo.split())

# --- Função para converter DF para Excel em memória ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Padronizado')
    processed_data = output.getvalue()
    return processed_data

# --- Interface de Upload ---
arquivo_upload = st.file_uploader("Carregue sua planilha (.xlsx)", type=["xlsx"])

if arquivo_upload is not None:
    try:
        # Lê o arquivo carregado
        df = pd.read_excel(arquivo_upload)
        
        st.write("### Prévia da Planilha:")
        st.dataframe(df.head())

        # Seleção da Coluna
        colunas = df.columns.tolist()
        coluna_alvo = st.selectbox("Selecione a coluna que contém os nomes:", colunas)

        if st.button("Padronizar Nomes"):
            with st.spinner('Processando...'):
                # Cria uma cópia para não alterar o original visualmente antes da hora
                df_novo = df.copy()
                
                # Aplica a limpeza
                df_novo[coluna_alvo] = df_novo[coluna_alvo].apply(limpar_nome)
                
                st.success("Concluído!")
                st.write("### Resultado:")
                st.dataframe(df_novo.head())

                # Botão de Download
                arquivo_excel = to_excel(df_novo)
                
                st.download_button(
                    label="📥 Baixar Planilha Padronizada",
                    data=arquivo_excel,
                    file_name="nomes_padronizados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
