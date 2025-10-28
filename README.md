# Prueba Técnica: Implementación de Chat IA con RAG

## CEPET System - 2025

Este repositorio contiene la solución desarrollada como parte de la **Prueba Técnica** solicitada por **CEPET System** para la implementación de un Asistente de Chat con Inteligencia Artificial que utiliza la arquitectura RAG.

---

## 1. Objetivo del Proyecto

El objetivo principal es diseñar e implementar un *chatbot* de inteligencia artificial (basado en LLM + RAG) que sea capaz de **responder preguntas basándose exclusivamente en documentos o datos** cargados en una base de datos o *vector store* propia, evitando la "alucinación" (devolviendo texto generado por el LLM solo por su contexto).

## 2. Requisitos Funcionales y Técnicos

### Requisitos Funcionales

* El asistente debe utilizar un modelo **LLM** (local o remoto).
* Debe incorporar la lógica **RAG** (Retrieval-Augmented Generation).
* **Fuente de Información:** Se utiliza una base de datos o *vector store* con la información proporcionada (se entregaron 10 documentos para trabajar).
    * *Nota:* Se requiere una fuente de información con **al menos 5 documentos**.
* **Interacción:** Debe permitir ingresar una pregunta y mostrar la respuesta de la IA **junto a los documentos usados** para generar dicha respuesta.
* **Formato de Respuesta:** La visualización de la respuesta y los documentos citados puede ser mediante HTML simple, Postman u otro método (e.g., JSON).

### Condiciones Técnicas

* **Herramientas y Frameworks:** Totalmente libres a elección, siempre y cuando se cumpla con el requisito central de **LLM + RAG**.
* **Lenguaje y Entorno:** Cualquier lenguaje o entorno es aceptable (e.g., Python, Node.js, no-code, etc.).
* **Comportamiento de la IA:** El LLM debe devolver texto generado **solo por el contexto proporcionado** (sin "alucinar").

---

## 3. Estructura de Base de Datos (Opcional: PostgreSQL)

Aunque la elección de la base de datos es libre (PostgreSQL es opcional), la solución se basa en la siguiente estructura de tablas, diseñada para gestionar documentos y sus metadatos (tipos, emisores, categorías y temas):


## 4. Documentación Adicional

* **Sentencias de BD:** Se deben documentar las sentencias de base de datos utilizadas.

---

## **Contenido del .env**

```ini
# Variables de la API de OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Variables de conexión a la Base de Datos
DB_HOST=
DB_PORT=5432
DB_NAME=
DB_USER=
DB_PASS=
```
## **Instrucciones de Uso**

1.  **Clonar el Repositorio:** `git clone https://github.com/IvanCaceresS/cepet-ia-rag-technical-test.git`
2.  **Descargar previamente nltk_data** `python download_nltk.py`
3.  **Construir e iniciar los contenedores** `docker-compose up --build -d`
4.  **Ejecutar la ingesta de datos** `docker-compose exec app python ingest.py`
5.  **Probar** `http://localhost:8501`

**Reiniar app** `docker-compose restart app`

**Ver logs del container en tiempo real** `docker-compose logs -f`

**Abrir la consola de postgreSQl** `docker exec -it rag_db psql -U admin -d rag_cepet_db`

- Listar todas las tablas: `\dt`
            `\dt categorias`
            `\dt documento_categoria`
            `\dt documento_tema`
            `\dt documentos`
            `\dt emisores`
            `\dt temas`
            `\dt tipos`
- Verificar la extensión pgvector: `\dx vector`
- Contar filas en tablas de metadatos: 
            `SELECT COUNT(*) FROM tipos;`
            `SELECT COUNT(*) FROM emisores;`
            `SELECT COUNT(*) FROM categorias;`
            `SELECT COUNT(*) FROM temas;`
- Ver datos de ejemplo en tablas de metadatos:
            `SELECT * FROM tipos LIMIT 5;`
            `SELECT * FROM emisores LIMIT 5;`
            `SELECT * FROM categorias LIMIT 10;`
            `SELECT * FROM temas LIMIT 10;`
- Contar el total de chunks: `SELECT COUNT(*) FROM documentos;`
- Verificar chunks sin cuerpo o sin vector:
            `SELECT COUNT(*) FROM documentos WHERE cuerpo IS NULL OR cuerpo = '';`
            `SELECT COUNT(*) FROM documentos WHERE search_vector IS NULL;`
- Verificar documentos originales procesados:
            `SELECT COUNT(DISTINCT titulo) FROM documentos;`
            `SELECT COUNT(DISTINCT url) FROM documentos;`
- Ver relaciones de ejemplo:
            `SELECT * FROM documento_categoria LIMIT 10;`
            `SELECT * FROM documento_tema LIMIT 10;`
