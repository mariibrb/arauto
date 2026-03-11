import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import io
import zipfile
import gc

# Configuração de Página
st.set_page_config(page_title="Arauto Fiscal | Matrioska Mode", layout="wide")

st.title("🎀 Arauto Fiscal")
st.markdown("#### Auditoria de XMLs em Camadas (Recursivo)")
st.divider()

def processar_arquivo(nome_arquivo, conteudo_bytes, lista_chaves):
    """
    Função recursiva para descascar ZIPs e localizar XMLs.
    """
    encontrados_local = []
    
    # Caso 1: O arquivo é um XML
    if nome_arquivo.lower().endswith('.xml'):
        try:
            tree = ET.fromstring(conteudo_bytes)
            elemento_chave = tree.find(".//{*}chNFe")
            if elemento_chave is not None:
                chave_xml = elemento_chave.text.strip()
                if chave_xml in lista_chaves:
                    encontrados_local.append({"nome": nome_arquivo, "bytes": conteudo_bytes})
        except Exception:
            pass # Ignora XMLs malformados ou de outros tipos
            
    # Caso 2: O arquivo é um ZIP (A Matrioska)
    elif nome_arquivo.lower().endswith('.zip'):
        try:
            with zipfile.ZipFile(io.BytesIO(conteudo_bytes)) as z:
                for zname in z.namelist():
                    with z.open(zname) as zfile:
                        # Chamada recursiva para o conteúdo do ZIP
                        encontrados_local.extend(
                            processar_arquivo(zname, zfile.read(), lista_chaves)
                        )
        except Exception as e:
            st.warning(f"Erro ao abrir sub-zip {nome_arquivo}: {e}")
            
    return encontrados_local

# Interface
uploaded_excel = st.file_uploader("1. Excel de Referência", type=['xlsx'])
uploaded_files = st.file_uploader("2. Arquivos (XML ou ZIP Matrioska)", type=['xml', 'zip'], accept_multiple_files=True)

if uploaded_excel and uploaded_files:
    try:
        df_ref = pd.read_excel(uploaded_excel, dtype=str)
        lista_chaves = set(df_ref.iloc[:, 0].str.strip().tolist()) # Set para busca O(1)
        st.info(f"Arauto preparado para buscar {len(lista_chaves)} chaves.")
    except Exception as e:
        st.error(f"Erro no Excel: {e}"); st.stop()

    todos_encontrados = []
    progresso = st.progress(0)
    
    if st.button("Iniciar Garimpo"):
        for i, file in enumerate(uploaded_files):
            # Processamento recursivo iniciado
            resultados = processar_arquivo(file.name, file.read(), lista_chaves)
            todos_encontrados.extend(resultados)
            progresso.progress((i + 1) / len(uploaded_files))
            gc.collect() # Limpeza de RAM por precaução

        st.divider()
        if todos_encontrados:
            st.success(f"O Arauto extraiu {len(todos_encontrados)} notas das matrioskas!")
            
            zip_final = io.BytesIO()
            with zipfile.ZipFile(zip_final, "w", zipfile.ZIP_DEFLATED) as zf:
                for item in todos_encontrados:
                    # Evita duplicados se o mesmo XML aparecer em zips diferentes
                    zf.writestr(item["nome"], item["bytes"])
            
            st.download_button(
                label="📦 Baixar Notas Extraídas (ZIP)",
                data=zip_final.getvalue(),
                file_name="arauto_extraido.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.error("Nenhuma nota correspondente foi encontrada nas camadas de compressão.")
