import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import io
import zipfile

# Configuração de Página - Identidade Arauto
st.set_page_config(page_title="Arauto Fiscal", layout="wide")

st.title("🎀 Arauto Fiscal")
st.markdown("#### O Mensageiro da Auditoria de Notas")
st.divider()

# Inputs do Usuário
col1, col2 = st.columns(2)

with col1:
    st.subheader("📜 Relação do Excel")
    uploaded_excel = st.file_uploader("Upload da lista de chaves", type=['xlsx'])

with col2:
    st.subheader("📂 Massa de XMLs")
    uploaded_xmls = st.file_uploader("Upload dos arquivos XML", type=['xml'], accept_multiple_files=True)

if uploaded_excel and uploaded_xmls:
    try:
        # Leitura rigorosa: tratando chaves como string para evitar notação científica
        df_ref = pd.read_excel(uploaded_excel, dtype=str)
        # Considera a primeira coluna como a lista de chaves
        lista_chaves = df_ref.iloc[:, 0].str.strip().tolist()
        st.info(f"Arauto: {len(lista_chaves)} chaves carregadas da lista oficial.")
    except Exception as e:
        st.error(f"Erro ao ler o pergaminho Excel: {e}")
        st.stop()

    encontrados = []
    
    # Barra de processamento em tempo real
    bar_progresso = st.progress(0)
    
    for i, xml_file in enumerate(uploaded_xmls):
        try:
            conteudo = xml_file.read()
            # Parsing do XML ignorando namespaces variados
            tree = ET.fromstring(conteudo)
            # Busca profunda pela tag da chave de acesso
            elemento_chave = tree.find(".//{*}chNFe")
            
            if elemento_chave is not None:
                chave_xml = elemento_chave.text.strip()
                if chave_xml in lista_chaves:
                    encontrados.append({"nome": xml_file.name, "bytes": conteudo})
            
            # Atualização da barra
            bar_progresso.progress((i + 1) / len(uploaded_xmls))
            
        except Exception as e:
            st.warning(f"O Arauto não conseguiu ler o arquivo {xml_file.name}: {e}")

    st.divider()
    
    # Resultado e Entrega
    if encontrados:
        st.success(f"O Arauto localizou {len(encontrados)} notas correspondentes!")
        
        # Compactação para facilitar o transporte dos dados
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in encontrados:
                zf.writestr(item["nome"], item["bytes"])
        
        st.download_button(
            label="📦 Resgatar Notas Localizadas (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="arauto_notas_filtradas.zip",
            mime="application/zip",
            use_container_width=True
        )
    else:
        st.error("Nenhuma nota da lista foi encontrada nos arquivos enviados.")
