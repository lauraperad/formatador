import streamlit as st
import pandas as pd
import unicodedata
import re
from io import BytesIO

# --- 1. Configuração da Página (Deve ser a primeira linha) ---
st.set_page_config(
    page_title="Padronizador Jurídico",
    page_icon="⚖️",
    layout="wide", # Layout largo para parecer dashboard
    initial_sidebar_state="expanded"
)

# --- CSS Personalizado para "Limpar" a interface ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
    }
    .reportview-container {
        background: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# --- Funções do Backend ---
def limpar_nome(texto):
    if not isinstance(texto, str):
        return str(texto) if pd.notna(texto) else ""
    nfkd_form = unicodedata.normalize('NFKD', texto)
    texto_sem_acento = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    texto_upper = texto_sem_acento.upper()
    texto_limpo = re.sub(r'[^A-Z\s]', '', texto_upper)
    return " ".join(texto_limpo.split())

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Padronizado')
    return output.getvalue()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2237/2237589.png", width=80)
    st.title("Configurações")
    st.markdown("---")
    
    # Upload na lateral
    arquivo_upload = st.file_uploader(
        "1. Carregue a Planilha (Excel ou CSV)", 
        type=["xlsx", "csv"]
    )
    
    st.markdown("---")
    st.info("ℹ️ **Ajuda:** O sistema remove acentos, cedilhas e caracteres especiais, mantendo apenas letras maiúsculas.")

# --- ÁREA PRINCIPAL ---
st.title("⚖️ Sistema de Padronização de Nomes")
st.markdown("##### Automação para tratamento de bases de dados jurídicas")

if arquivo_upload is None:
    # Tela de boas-vindas quando não tem arquivo
    st.warning("👈 Por favor, faça o upload da planilha na barra lateral para começar.")
    st.markdown("### O que este sistema faz?")
    col1, col2, col3 = st.columns(3)
    col1.metric("1. Remove Acentos", "João -> JOAO")
    col2.metric("2. Remove Especiais", "@Dra. -> DRA")
    col3.metric("3. Padroniza", "Caixa Alta")

else:
    try:
        # Leitura do arquivo
        if arquivo_upload.name.endswith('.csv'):
            df = pd.read_csv(arquivo_upload)
        else:
            df = pd.read_excel(arquivo_upload)

        # Lógica de seleção da coluna
        colunas = df.columns.tolist()
        indice_sugerido = 2 if len(colunas) >= 3 else 0
        
        # Coloca a seleção na Barra Lateral também, para não poluir o centro
        with st.sidebar:
            if len(colunas) < 3:
                st.warning("⚠️ Planilha com menos de 3 colunas.")
            
            coluna_alvo = st.selectbox(
                "2. Selecione a coluna de NOMES:", 
                colunas, 
                index=indice_sugerido
            )
            
            # Botão de Processar grande na lateral
            processar = st.button("🚀 Padronizar Agora")

        # --- VISUALIZAÇÃO DOS DADOS ---
        
        # Se o botão ainda não foi clicado, mostra apenas a prévia
        if not processar:
            st.subheader("Visualização dos Dados Originais")
            st.markdown(f"**Total de linhas encontradas:** `{len(df)}`")
            st.dataframe(df.head(10), use_container_width=True)

        # Se clicou em processar
        else:
            with st.spinner('Processando dados...'):
                df_novo = df.copy()
                df_novo[coluna_alvo] = df_novo[coluna_alvo].apply(limpar_nome)
                
                # --- DASHBOARD DE RESULTADOS ---
                st.success("✅ Processamento concluído com sucesso!")
                
                # Métricas
                m1, m2, m3 = st.columns(3)
                m1.metric("Linhas Processadas", len(df_novo))
                m2.metric("Coluna Tratada", coluna_alvo)
                m3.metric("Status", "Finalizado", delta="OK")
                
                st.markdown("---")
                
                # Comparativo "Antes e Depois"
                st.subheader("🔍 Comparativo (Amostra)")
                col_esq, col_dir = st.columns(2)
                
                with col_esq:
                    st.markdown("**Original (Primeiros 5):**")
                    st.dataframe(df[coluna_alvo].head(), use_container_width=True)
                
                with col_dir:
                    st.markdown("**Padronizado (Primeiros 5):**")
                    st.dataframe(df_novo[coluna_alvo].head(), use_container_width=True)
                
                st.markdown("---")
                
                # Área de Download Centralizada
                st.subheader("📥 Download")
                col_dwn, _ = st.columns([1, 2]) # Coluna menor para o botão não ficar gigante
                with col_dwn:
                    st.download_button(
                        label="Baixar Planilha Pronta (.xlsx)",
                        data=to_excel(df_novo),
                        file_name="Juizes_Padronizados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"❌ Ocorreu um erro ao ler o arquivo: {e}")
