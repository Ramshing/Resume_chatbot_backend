--
-- PostgreSQL database dump
--

-- Dumped from database version 15.3
-- Dumped by pg_dump version 15.3

-- Started on 2026-05-07 16:03:52

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 2 (class 3079 OID 49385)
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- TOC entry 3614 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- TOC entry 3 (class 3079 OID 49596)
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- TOC entry 3615 (class 0 OID 0)
-- Dependencies: 3
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 218 (class 1259 OID 49432)
-- Name: chunks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chunks (
    chunk_id integer NOT NULL,
    resume_id uuid,
    chunk_text text,
    chunk_index integer,
    metadata jsonb,
    embedding public.vector(384),
    tsv tsvector
);


ALTER TABLE public.chunks OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 49431)
-- Name: chunks_chunk_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chunks_chunk_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.chunks_chunk_id_seq OWNER TO postgres;

--
-- TOC entry 3616 (class 0 OID 0)
-- Dependencies: 217
-- Name: chunks_chunk_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chunks_chunk_id_seq OWNED BY public.chunks.chunk_id;


--
-- TOC entry 216 (class 1259 OID 49422)
-- Name: resumes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resumes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    candidate_name text,
    full_text text,
    skills jsonb,
    experience_months integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    file_hash text,
    file_path text
);


ALTER TABLE public.resumes OWNER TO postgres;

--
-- TOC entry 3457 (class 2604 OID 49435)
-- Name: chunks chunk_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chunks ALTER COLUMN chunk_id SET DEFAULT nextval('public.chunks_chunk_id_seq'::regclass);


--
-- TOC entry 3463 (class 2606 OID 49439)
-- Name: chunks chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chunks
    ADD CONSTRAINT chunks_pkey PRIMARY KEY (chunk_id);


--
-- TOC entry 3459 (class 2606 OID 49448)
-- Name: resumes resumes_file_hash_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_file_hash_key UNIQUE (file_hash);


--
-- TOC entry 3461 (class 2606 OID 49430)
-- Name: resumes resumes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_pkey PRIMARY KEY (id);


--
-- TOC entry 3464 (class 1259 OID 49924)
-- Name: idx_chunks_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chunks_embedding ON public.chunks USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- TOC entry 3465 (class 1259 OID 49925)
-- Name: idx_chunks_tsv; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chunks_tsv ON public.chunks USING gin (tsv);


--
-- TOC entry 3466 (class 2606 OID 49440)
-- Name: chunks chunks_resume_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chunks
    ADD CONSTRAINT chunks_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(id) ON DELETE CASCADE;


-- Completed on 2026-05-07 16:03:53

--
-- PostgreSQL database dump complete
--

