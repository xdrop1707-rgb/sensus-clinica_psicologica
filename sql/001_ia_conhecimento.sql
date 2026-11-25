create extension if not exists vector with schema extensions;

create table if not exists public.ia_conhecimento (
    id           bigint generated always as identity primary key,
    fonte        text        not null,              -- nome do arquivo de origem
    chunk_index  int         not null,              -- posição do trecho dentro da fonte
    conteudo     text        not null,
    embedding    extensions.vector(768) not null,
    criado_em    timestamptz not null default now(),
    unique (fonte, chunk_index)                     -- permite reingestão idempotente (upsert)
);

create index if not exists ia_conhecimento_embedding_idx
    on public.ia_conhecimento
    using hnsw (embedding extensions.vector_cosine_ops);


alter table public.ia_conhecimento enable row level security;
revoke all on public.ia_conhecimento from anon, authenticated;

create or replace function public.buscar_conhecimento(
    query_embedding   extensions.vector(768),
    match_count       int   default 4,
    match_threshold   float default 0.55
)
returns table (id bigint, fonte text, conteudo text, similaridade double precision)
language sql
stable
set search_path = public, extensions
as $$
    select
        c.id,
        c.fonte,
        c.conteudo,
        1 - (c.embedding <=> query_embedding) as similaridade
    from public.ia_conhecimento c
    where 1 - (c.embedding <=> query_embedding) > match_threshold
    order by c.embedding <=> query_embedding
    limit least(match_count, 10);
$$;

revoke execute on function public.buscar_conhecimento(extensions.vector, int, float) from public, anon, authenticated;
grant  execute on function public.buscar_conhecimento(extensions.vector, int, float) to service_role;
