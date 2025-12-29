import streamlit as st
import pandas as pd
import unicodedata
import re
from io import BytesIO

# --- 1. Configuração da Página ---
st.set_page_config(
    page_title="Padronizador Jurídico",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Personalizado ---
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
    # 1. SEGURANÇA: Se o valor for nulo (vazio/NaN), retorna vazio e não faz nada.
    # Isso garante que a linha não seja excluída e mantém o alinhamento.
    if pd.isna(texto) or texto == "":
        return ""
    
    # Garante que é string (caso tenha algum número perdido no meio dos nomes)
    texto = str(texto)
    
    # 2. Normaliza (separa acentos)
    nfkd_form = unicodedata.normalize('NFKD', texto)
    texto_sem_acento = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    # 3. Caixa alta
    texto_upper = texto_sem_acento.upper()
    
    # 4. Remove caracteres especiais (mantém apenas letras e espaços)
    texto_limpo = re.sub(r'[^A-Z\s]', '', texto_upper)
    
    # 5. Remove espaços duplos
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
    
    arquivo_upload = st.file_uploader(
        "1. Carregue a Planilha", 
        type=["xlsx", "csv"]
    )
    
    st.markdown("---")
    st.info("ℹ️ **Nota:** Linhas vazias serão mantidas vazias para preservar o alinhamento com os números dos processos.")

# --- ÁREA PRINCIPAL ---
st.title("⚖️ Sistema de Padronização de Nomes")
st.markdown("##### Automação para tratamento de bases de dados jurídicas")

if arquivo_upload is None:
    st.warning("👈 Por favor, faça o upload da planilha na barra lateral para começar.")
    st.markdown("### Funcionalidades:")
    col1, col2, col3 = st.columns(3)
    col1.metric("1. Remove Acentos", "JOÃO -> JOAO")
    col2.metric("2. Preserva Vazios", "Mantém a ordem")
    col3.metric("3. Padroniza", "Caixa Alta")

else:
    try:
        # Leitura do arquivo
        if arquivo_upload.name.endswith('.csv'):
            df = pd.read_csv(arquivo_upload)
        else:
            df = pd.read_excel(arquivo_upload)

        colunas = df.columns.tolist()
        indice_sugerido = 2 if len(colunas) >= 3 else 0
        
        with st.sidebar:
            if len(colunas) < 3:
                st.warning("⚠️ Planilha com menos de 3 colunas.")
            
            coluna_alvo = st.selectbox(
                "2. Selecione a coluna de NOMES:", 
                colunas, 
                index=indice_sugerido
            )
            
            processar = st.button("🚀 Padronizar Agora")

        # --- VISUALIZAÇÃO ---
        if not processar:
            st.subheader("Visualização dos Dados Originais")
            st.info(f"O sistema identificou **{len(df)}** linhas. Nenhuma linha será excluída.")
            st.dataframe(df.head(10), use_container_width=True)

        else:
            with st.spinner('Processando dados e mantendo alinhamento...'):
                df_novo = df.copy()
                
                # Aplica a limpeza mantendo o índice original
                df_novo[coluna_alvo] = df_novo[coluna_alvo].apply(limpar_nome)
                
                st.success("✅ Processamento concluído!")
                
                # Métricas
                m1, m2 = st.columns(2)
                m1.metric("Total de Linhas", len(df_novo))
                # Conta quantos vazios existem para conferência
                vazios = df_novo[coluna_alvo].isna().sum() + (df_novo[coluna_alvo] == "").sum()
                m2.metric("Células Vazias Mantidas", int(vazios))
                
                st.markdown("---")
                
                # Comparativo
                st.subheader("🔍 Comparativo (Amostra)")
                col_esq, col_dir = st.columns(2)
                with col_esq:
                    st.markdown("**Original:**")
                    st.dataframe(df[[coluna_alvo]].head(10), use_container_width=True)
                with col_dir:
                    st.markdown("**Padronizado:**")
                    st.dataframe(df_novo[[coluna_alvo]].head(10), use_container_width=True)
                
                st.markdown("---")
                
                # Download
                st.subheader("📥 Download")
                col_dwn, _ = st.columns([1, 2])
                with col_dwn:
                    st.download_button(
                        label="Baixar Planilha (.xlsx)",
                        data=to_excel(df_novo),
                        file_name="Juizes_Padronizados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"❌ Erro ao ler arquivo: {e}")
