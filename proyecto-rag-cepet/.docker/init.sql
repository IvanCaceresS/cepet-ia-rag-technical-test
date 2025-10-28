-- Extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Metadatos
CREATE TABLE IF NOT EXISTS tipos (
    id_tipo SERIAL PRIMARY KEY,
    nombre_tipo TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS emisores (
    id_emisor SERIAL PRIMARY KEY,
    nombre_emisor TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS categorias (
    id_categoria SERIAL PRIMARY KEY,
    nombre_categoria TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS temas (
    id_tema SERIAL PRIMARY KEY,
    nombre_tema TEXT NOT NULL UNIQUE
);

-- DOCUMENTOS
CREATE TABLE IF NOT EXISTS documentos (
    id_documento SERIAL PRIMARY KEY,
    titulo TEXT,
    fecha DATE,
    tipo_id INT REFERENCES tipos(id_tipo),
    cuerpo TEXT,
    url TEXT,
    emisor_id INT REFERENCES emisores(id_emisor),
    search_vector vector(1536) 
);

-- Tablas de unión (documento con sus categorías y temas)
CREATE TABLE IF NOT EXISTS documento_categoria (
    documento_id INT REFERENCES documentos(id_documento) ON DELETE CASCADE,
    categoria_id INT REFERENCES categorias(id_categoria) ON DELETE CASCADE,
    PRIMARY KEY (documento_id, categoria_id)
);

CREATE TABLE IF NOT EXISTS documento_tema (
    documento_id INT REFERENCES documentos(id_documento) ON DELETE CASCADE,
    tema_id INT REFERENCES temas(id_tema) ON DELETE CASCADE,
    PRIMARY KEY (documento_id, tema_id)
);

-- Indices para búsquedas de llaves foráneas
CREATE INDEX IF NOT EXISTS idx_documentos_tipo_id ON documentos(tipo_id);
CREATE INDEX IF NOT EXISTS idx_documentos_emisor_id ON documentos(emisor_id);