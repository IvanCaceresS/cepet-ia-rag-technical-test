import os
import json
import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def get_or_create_metadata_id(cursor, table_name, id_column_name, value_column_name, value):
    cursor.execute(f"SELECT {id_column_name} FROM {table_name} WHERE {value_column_name} = %s", (value,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute(f"INSERT INTO {table_name} ({value_column_name}) VALUES (%s) RETURNING {id_column_name}", (value,))
        return cursor.fetchone()[0]

def process_and_ingest():
    print("Iniciando la ingesta de datos...")
    conn = get_db_connection()
    if conn is None:
        return

    register_vector(conn)
    
    cursor = conn.cursor()

    try:
        # Cargar el manifiesto
        with open('manifest.json', 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        print(f"Manifiesto cargado. Procesando {len(manifest)} documentos.")
        embeddings_model = OpenAIEmbeddings()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        for item in manifest:
            print(f"--- Procesando: {item['titulo']} ---")
            
            # --- POBLAR METADATOS ---
            tipo_id = get_or_create_metadata_id(cursor, "tipos", "id_tipo", "nombre_tipo", item["tipo"])
            emisor_id = get_or_create_metadata_id(cursor, "emisores", "id_emisor", "nombre_emisor", item["emisor"])

            categoria_ids = [get_or_create_metadata_id(cursor, "categorias", "id_categoria", "nombre_categoria", cat) for cat in item["categorias"]]
            tema_ids = [get_or_create_metadata_id(cursor, "temas", "id_tema", "nombre_tema", tema) for tema in item["temas"]]

            # --- CARGAR Y DIVIDIR DOCUMENTO EN CHUNKS ---
            print(f"Cargando y dividiendo el archivo: {item['archivo']}...")
            loader = UnstructuredLoader(item["archivo"], languages=['es'])
            docs = loader.load()
            chunks = text_splitter.split_documents(docs)
            print(f"Archivo dividido en {len(chunks)} chunks.")

            # --- GENERAR EMBEDDINGS Y PREPARAR DATOS PARA INGESTA ---

            chunk_texts = [chunk.page_content for chunk in chunks]
            
            print("Generando embeddings (esto puede tardar)...")
            chunk_embeddings = embeddings_model.embed_documents(chunk_texts)
            print("Embeddings generados.")

            documentos_data = []
            for i, chunk_text in enumerate(chunk_texts):
                documentos_data.append((
                    item["titulo"],
                    item["fecha"],
                    tipo_id,
                    chunk_text,
                    item["archivo"],
                    emisor_id,
                    chunk_embeddings[i]
                ))

            # --- INSERTAR CHUNKS EN LA BBDD ---
            print(f"Insertando {len(documentos_data)} chunks en la BBDD...")

            sql_insert_documentos = """
                INSERT INTO documentos (
                    titulo, fecha, tipo_id, cuerpo, url, emisor_id, search_vector
                ) VALUES %s RETURNING id_documento
            """
            
            new_doc_ids = execute_values(
                cursor, 
                sql_insert_documentos, 
                documentos_data, 
                template=None, 
                page_size=100,
                fetch=True
            )

            doc_categoria_data = []
            doc_tema_data = []

            for (doc_id,) in new_doc_ids:
                for cat_id in categoria_ids:
                    doc_categoria_data.append((doc_id, cat_id))
                for tema_id in tema_ids:
                    doc_tema_data.append((doc_id, tema_id))

            # INSERTAR RELACIONES DE CATEGORÍA
            sql_insert_categorias = "INSERT INTO documento_categoria (documento_id, categoria_id) VALUES %s ON CONFLICT DO NOTHING"
            execute_values(cursor, sql_insert_categorias, doc_categoria_data, page_size=100)

            # INSERTAR RELACIONES DE TEMA
            sql_insert_temas = "INSERT INTO documento_tema (documento_id, tema_id) VALUES %s ON CONFLICT DO NOTHING"
            execute_values(cursor, sql_insert_temas, doc_tema_data, page_size=100)
            
            print(f"Documento '{item['titulo']}' ingestado exitosamente.")

        conn.commit()
        print("\n¡Ingesta de datos completada exitosamente!")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error durante la ingesta: {error}")
        conn.rollback()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    print("ADVERTENCIA: Limpiando tablas de la base de datos antes de la ingesta...")
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE tipos, emisores, categorias, temas, documentos, documento_categoria, documento_tema RESTART IDENTITY CASCADE")
            conn.commit()
        conn.close()
        print("Tablas limpias.")
        process_and_ingest()