-- Table: public.resumes

-- DROP TABLE IF EXISTS public.resumes;

CREATE TABLE IF NOT EXISTS public.resumes
(
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    candidate_name text COLLATE pg_catalog."default",
    full_text text COLLATE pg_catalog."default",
    skills jsonb,
    experience_months integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    file_hash text COLLATE pg_catalog."default",
    file_path text COLLATE pg_catalog."default",
    CONSTRAINT resumes_pkey PRIMARY KEY (id),
    CONSTRAINT resumes_file_hash_key UNIQUE (file_hash)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.resumes
    OWNER to postgres;