"""Ingestão da base de conhecimento do Sensus no Supabase.

Uso:  python -m ia.ingestao [--pasta dados/conhecimento]
Lê .md/.txt/.pdf, divide em trechos, gera embeddings no Gemini e grava (upsert) em ia_conhecimento.
Arquivos que começam com "_" são ignorados. Pode ser reexecutado sem duplicar dados.
"""
import argparse
import re
from pathlib import Path

from .clientes import supabase_admin
from .embeddings import embed_documentos, para_pgvector

TABELA = "ia_conhecimento"
EXTENSOES = {".md", ".txt", ".pdf"}
LOTE_INSERT = 50


def _janela(texto: str, tamanho: int, overlap: int) -> list[str]:
    passo = max(tamanho - overlap, 1)
    return [texto[i : i + tamanho] for i in range(0, len(texto), passo)]


def dividir_em_chunks(texto: str, tamanho: int = 900, overlap: int = 150) -> list[str]:
    """Agrupa parágrafos até `tamanho` caracteres, repetindo o final do trecho anterior (overlap)."""
    paragrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    chunks: list[str] = []
    atual = ""
    for p in paragrafos:
        if len(p) > tamanho:  # parágrafo gigante: janela deslizante
            if atual:
                chunks.append(atual)
                atual = ""
            chunks.extend(_janela(p, tamanho, overlap))
            continue
        if atual and len(atual) + 2 + len(p) > tamanho:
            chunks.append(atual)
            cauda = atual[-overlap:] if overlap else ""
            if " " in cauda:  # evita começar no meio de uma palavra
                cauda = cauda.split(" ", 1)[1]
            atual = f"{cauda}\n\n{p}" if cauda else p
        else:
            atual = f"{atual}\n\n{p}" if atual else p
    if atual:
        chunks.append(atual)
    return chunks


def _ler(arquivo: Path) -> str:
    if arquivo.suffix.lower() == ".pdf":
        from pypdf import PdfReader  # import tardio: só exigido se houver PDF

        return "\n\n".join((p.extract_text() or "") for p in PdfReader(str(arquivo)).pages)
    return arquivo.read_text(encoding="utf-8")


def ingerir_arquivo(arquivo: Path, pasta_base: Path) -> int:
    fonte = arquivo.relative_to(pasta_base).as_posix()
    chunks = dividir_em_chunks(_ler(arquivo))
    if not chunks:
        print(f"  - {fonte}: vazio, ignorado")
        return 0

    vetores = embed_documentos(chunks)
    linhas = [
        {"fonte": fonte, "chunk_index": i, "conteudo": c, "embedding": para_pgvector(v)}
        for i, (c, v) in enumerate(zip(chunks, vetores, strict=True))
    ]
    sb = supabase_admin()
    for i in range(0, len(linhas), LOTE_INSERT):
        sb.table(TABELA).upsert(linhas[i : i + LOTE_INSERT], on_conflict="fonte,chunk_index").execute()
    # Remove trechos "sobrando" de uma versão anterior maior do mesmo arquivo
    sb.table(TABELA).delete().eq("fonte", fonte).gte("chunk_index", len(chunks)).execute()
    print(f"  - {fonte}: {len(chunks)} trechos")
    return len(chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestão da base de conhecimento do Sensus")
    parser.add_argument("--pasta", default="dados/conhecimento")
    pasta = Path(parser.parse_args().pasta)

    arquivos = sorted(
        p for p in pasta.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSOES and not p.name.startswith("_")
    )
    if not arquivos:
        raise SystemExit(f"Nenhum arquivo .md/.txt/.pdf encontrado em {pasta} (arquivos iniciados por '_' são ignorados).")

    print(f"Ingerindo {len(arquivos)} arquivo(s) de {pasta}...")
    total = sum(ingerir_arquivo(a, pasta) for a in arquivos)
    print(f"Pronto: {total} trechos gravados.")


if __name__ == "__main__":
    main()
