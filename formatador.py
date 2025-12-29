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

# --- CSS Personalizado (Adaptável) ---
# Aqui removemos a cor de fundo fixa para o Modo Escuro funcionar
st.markdown("""
<style>
    /* Botão vermelho que funciona bem no claro e no escuro */
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        border: none;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #FF2B2B;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- Funções do Backend ---
def limpar_nome(texto):
    if pd.isna(texto) or texto == "":
        return ""
    
    texto_str = str(texto)
    
    # REGRA DE EXCEÇÃO
    frase_proibida = "informação indisponível no site"
    if frase_proibida in texto_str.lower():
        return texto_str 
    
    # PADRONIZAÇÃO
    nfkd_form = unicodedata.normalize('NFKD', texto_str)
    texto_sem_acento = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    texto_upper = texto_sem_acento.upper()
    texto_limpo = re.sub(r'[^A-Z\s]', '', texto_upper)
    return " ".join(texto_limpo.split())

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Padronizado')
    return output.getvalue()

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2237/2237589.png", width=80)
    st.title("Configurações")
    st.markdown("---")
    
    arquivo_upload = st.file_uploader(
        "1. Carregue a Planilha", 
        type=["xlsx", "csv"]
    )
    
    st.markdown("---")
    st.markdown("### Regras Ativas:")
    st.success("✅ **Preservar Vazios:** Mantém alinhamento.")
    st.warning("⚠️ **Exceção:** Frases 'Informação indisponível...' não serão alteradas.")

# --- ÁREA PRINCIPAL ---
st.title("⚖️ Sistema de Padronização de Nomes")
st.markdown("##### Automação para tratamento de bases de dados jurídicas")

if arquivo_upload is None:
    st.warning("👈 Por favor, faça o upload da planilha na barra lateral para começar.")
    st.markdown("### O que o robô vai fazer?")
    col1, col2, col3 = st.columns(3)
    
    # Exemplo visual ajustado para "João"
    col1.metric("1. Remove Acentos", "João -> JOAO")
    col2.metric("2. Ignorar Vazios", "Mantém a linha")
    col3.metric("3. Ignorar Aviso", "Mantém 'Inf. Indisponível'")

else:
    try:
        # Leitura
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

        # Visualização
        if not processar:
            st.subheader("Visualização dos Dados Originais")
            st.info(f"O sistema identificou **{len(df)}** linhas.")
            st.dataframe(df.head(10), use_container_width=True)

        else:
            with st.spinner('Aplicando regras de negócio...'):
                df_novo = df.copy()
                df_novo[coluna_alvo] = df_novo[coluna_alvo].apply(limpar_nome)
                
                # Métricas
                total_linhas = len(df_novo)
                vazios = df_novo[coluna_alvo].isna().sum() + (df_novo[coluna_alvo] == "").sum()
                preservados = df_novo[coluna_alvo].astype(str).str.lower().str.contains("informação indisponível no site").sum()
                
                st.success("✅ Processamento concluído!")
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Processado", total_linhas)
                m2.metric("Vazios Mantidos", int(vazios))
                m3.metric("Avisos Preservados", int(preservados), delta="Regra de Exceção")
                
                st.markdown("---")
                
                st.subheader("🔍 Auditoria Visual")
                col_esq, col_dir = st.columns(2)
                with col_esq:
                    st.markdown("**Original:**")
                    st.dataframe(df[[coluna_alvo]].head(10), use_container_width=True)
                with col_dir:
                    st.markdown("**Padronizado (Resultado):**")
                    st.dataframe(df_novo[[coluna_alvo]].head(10), use_container_width=True)
                
                st.markdown("---")
                
                st.subheader("📥 Download")
                col_dwn, _ = st.columns([1, 2])
                with col_dwn:
                    st.download_button(
                        label="Baixar Planilha Pronta (.xlsx)",
                        data=to_excel(df_novo),
                        file_name="Juizes_Padronizados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {e}")
