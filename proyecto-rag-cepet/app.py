import os
import streamlit as st
from dotenv import load_dotenv
import psycopg2
from pgvector.psycopg2 import register_vector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from typing import List

load_dotenv()

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]

llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
embeddings_model = OpenAIEmbeddings()

class CustomPGVectorRetriever(BaseRetriever):
    k: int = 5

    def _get_db_connection(self):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            register_vector(conn)
            return conn
        except psycopg2.OperationalError as e:
            st.error(f"Error conectando a la BBDD: {e}")
            print(f"Error conectando a la BBDD: {e}")
            return None

    def _get_relevant_documents(self, query: str) -> List[Document]:
        print(f"\n--- Retriever: Recibida query: '{query}' ---", flush=True)
        conn = self._get_db_connection()
        if not conn:
            print("Retriever: Falló la conexión a la BBDD.", flush=True)
            return []
        else:
            print("Retriever: Conexión a BBDD establecida.", flush=True)

        try:
            with conn.cursor() as cursor:
                print("Retriever: Generando embedding para la consulta...", flush=True)
                query_embedding = embeddings_model.embed_query(query)
                print(f"Retriever: Embedding generado (primeros 5): {query_embedding[:5]}...", flush=True)

                sql = """
                    SELECT
                        cuerpo,
                        titulo,
                        url,
                        fecha,
                        search_vector <=> %s::vector AS distance
                    FROM documentos
                    ORDER BY distance ASC
                    LIMIT %s;
                """
                print(f"Retriever: Ejecutando SQL con k={self.k}...")
                query_embedding_str = str(query_embedding)
                cursor.execute(sql, (query_embedding_str, self.k))
                print("Retriever: Consulta SQL ejecutada.")
                results = cursor.fetchall()
                print(f"Retriever: Resultados obtenidos de BBDD ({len(results)} filas).")

                langchain_docs = []
                for row in results:
                    cuerpo, titulo, url, fecha, distance = row
                    metadata = {
                        "titulo_documento": titulo,
                        "url_documento": url.replace("docs/", "") if url else "N/A",
                        "fecha_documento": str(fecha) if fecha else "N/A",
                        "score": 1 - distance
                    }
                    langchain_docs.append(Document(page_content=cuerpo, metadata=metadata))

                print(f"Retriever: Encontrados {len(langchain_docs)} documentos para la query.")
                return langchain_docs

        except Exception as e:
            st.error(f"Error durante la búsqueda en BBDD: {e}")
            print(f"Error durante la búsqueda en BBDD: {e}")
            return []
        finally:
            if conn:
                conn.close()
                print("Retriever: Conexión BBDD cerrada.")

try:
    retriever = CustomPGVectorRetriever(k=5)
    print("CustomPGVectorRetriever instanciado.")
except Exception as e:
    st.error(f"Error al instanciar el retriever personalizado: {e}")
    print(f"Error al instanciar el retriever personalizado: {e}")
    st.stop()

# Prompt
template = """
Eres un asistente experto en documentos oficiales chilenos.
Responde la pregunta del usuario basándote únicamente en el siguiente contexto extraído de la base de datos.
Si la información no se encuentra en el contexto, di "No tengo información sobre eso en los documentos consultados".
Al final de tu respuesta, cita SOLO la fuente o fuentes DIRECTAMENTE usadas para la respuesta (título y archivo).

Contexto:
{context}

Pregunta:
{question}

Respuesta concisa y directa:
"""
prompt = ChatPromptTemplate.from_template(template)

def format_docs_custom(docs: List[Document]):
    context_str = ""
    sources_metadata = []
    if not docs:
        return {"context": "No se encontraron documentos relevantes.", "sources_metadata": []}

    for doc in docs:
        context_str += f"\n---\nExtracto de: {doc.metadata.get('titulo_documento', 'N/A')}\nArchivo: {doc.metadata.get('url_documento', 'N/A')}\nTexto: {doc.page_content}\n"
        sources_metadata.append(doc.metadata)

    context_str += "\n---\n"
    return {"context": context_str, "sources_metadata": sources_metadata}

# Cadena RAG -> Combinación de recuperación y generación
rag_chain = (
    {"question": RunnablePassthrough()}
    | RunnablePassthrough.assign(
        retrieved_docs=lambda x: retriever.invoke(x["question"])
    )
    | RunnablePassthrough.assign(
        formatted_context=lambda x: format_docs_custom(x["retrieved_docs"])
    )
    | RunnableParallel(
        {
            "context": lambda x: x["formatted_context"]["context"],
            "question": lambda x: x["question"],
        },
        retrieved_metadata=lambda x: x["formatted_context"]["sources_metadata"],
    )
    | {
        "answer": prompt | llm | StrOutputParser(),
        "retrieved_sources": lambda x: x["retrieved_metadata"],
    }
)

def format_response_for_display(result_dict):
    answer = result_dict.get("answer", "No se generó respuesta.")
    sources = result_dict.get("retrieved_sources", [])
    unique_sources = set()
    if sources:
        for meta in sources:
            title = meta.get('titulo_documento', 'Título Desconocido')
            file = meta.get('url_documento', 'Archivo Desconocido')
            unique_sources.add((title, file))
    formatted_string = f"{answer}\n\n---\n**Fuentes Consultadas (Contexto Recuperado):**\n"
    if unique_sources:
        sorted_sources = sorted(list(unique_sources))
        for tit, arch in sorted_sources:
            formatted_string += f"- {tit} (Archivo: {arch})\n"
    else:
        formatted_string += "- *No se recuperaron fuentes específicas del contexto.*\n"
    return formatted_string


# --- GUI USANDO Streamlit ---
st.set_page_config(page_title="Chatbot CEPET (RAG + Custom SQL)", layout="wide")
st.title("🤖 Chatbot CEPET (IA + RAG - SQL Directo)")
st.caption(f"Conectado a PostgreSQL: {DB_NAME} (Tabla: documentos)")

if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt_input := st.chat_input("¿Qué quieres saber sobre los documentos?"):
    st.session_state.messages.append({"role": "user", "content": prompt_input})
    with st.spinner("Buscando en base de datos (SQL directo) y generando respuesta..."):
        try:
            print(f"\n--- APP: Invocando rag_chain con la pregunta: '{prompt_input}' ---")
            raw_result = rag_chain.invoke(prompt_input)
            st.session_state.messages.append({"role": "assistant", "content": raw_result})
        except Exception as e:
            st.error(f"Error al procesar la pregunta: {e}")
            print(f"ERROR: {e}")
            error_message = "Lo siento, ocurrió un error al procesar tu pregunta."
            st.session_state.messages.append({"role": "assistant", "content": error_message})

# --- MOSTRAR HISTORIAL ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        if message["role"] == "assistant" and isinstance(content, dict):
            try:
                formatted_text = format_response_for_display(content)
                st.markdown(formatted_text)
            except Exception as format_error:
                st.error(f"Error al formatear la respuesta: {format_error}")
                st.write("Contenido crudo:")
                st.write(content)
        else:
            st.markdown(str(content))