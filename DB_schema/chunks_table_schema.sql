-- Table: public.chunks

-- DROP TABLE IF EXISTS public.chunks;

CREATE TABLE IF NOT EXISTS public.chunks
(
    chunk_id integer NOT NULL DEFAULT nextval('chunks_chunk_id_seq'::regclass),
    resume_id uuid,
    chunk_text text COLLATE pg_catalog."default",
    chunk_index integer,
    metadata jsonb,
    embedding vector(384),
    tsv tsvector,
    CONSTRAINT chunks_pkey PRIMARY KEY (chunk_id),
    CONSTRAINT chunks_resume_id_fkey FOREIGN KEY (resume_id)
        REFERENCES public.resumes (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.chunks
    OWNER to postgres;
-- Index: idx_chunks_embedding

-- DROP INDEX IF EXISTS public.idx_chunks_embedding;

CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON public.chunks USING ivfflat
    (embedding vector_cosine_ops)
    TABLESPACE pg_default;
-- Index: idx_chunks_tsv

-- DROP INDEX IF EXISTS public.idx_chunks_tsv;

CREATE INDEX IF NOT EXISTS idx_chunks_tsv
    ON public.chunks USING gin
    (tsv)
    TABLESPACE pg_default;