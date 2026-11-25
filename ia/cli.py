"""Chat de teste no terminal (substitui os loops dos scripts 03/04).

Uso:  python -m ia.cli [--debug]
--debug mostra a similaridade máxima e as fontes, útil para calibrar RAG_MIN_SIMILARITY.
"""
import argparse

from .agente import ErroServicoIA, Turno, responder


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    debug = parser.parse_args().debug

    historico: list[Turno] = []
    print("=" * 60)
    print("Assistente Sensus (teste). Digite 'sair' para encerrar.")
    print("=" * 60)
    while True:
        pergunta = input("\nVocê: ").strip()
        if pergunta.lower() in {"sair", "exit"}:
            print("Até logo!")
            break
        if not pergunta:
            continue
        try:
            r = responder(pergunta, historico)
        except ValueError as e:
            print(f"[entrada inválida] {e}")
            continue
        except ErroServicoIA as e:
            print(f"[erro de serviço: {e}] veja o log para detalhes")
            continue

        print(f"\nAssistente: {r.texto}")
        if debug:
            print(f"   [motivo={r.motivo} | sim_max={r.similaridade_max} | fontes={r.fontes}]")
        if r.motivo == "ok":  # só guarda no histórico respostas geradas dentro do escopo
            historico += [Turno("user", pergunta), Turno("model", r.texto)]


if __name__ == "__main__":
    main()
