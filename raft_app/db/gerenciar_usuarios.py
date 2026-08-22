"""
gerenciar_usuarios.py — cria e lista usuários do RAFT direto pelo terminal.
Use isto pra cadastrar o primeiro admin e os operadores, sem precisar de
uma tela de "criar usuário" pública (que seria um risco de segurança).

Uso:
    python db/gerenciar_usuarios.py criar --username joao --senha "SenhaForte123" --nome "João Pedro" --perfil ADMINISTRADOR
    python db/gerenciar_usuarios.py listar
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import criar_usuario
from db_utils import query_df, DB_PATH


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="comando", required=True)

    p_criar = sub.add_parser("criar")
    p_criar.add_argument("--username", required=True)
    p_criar.add_argument("--senha", required=True)
    p_criar.add_argument("--nome", required=True)
    p_criar.add_argument("--perfil", required=True,
                          choices=["OPERADOR", "PCP", "ALMOXARIFADO", "ADMINISTRADOR"])

    sub.add_parser("listar")

    args = parser.parse_args()

    print(f"Banco em uso: {DB_PATH.resolve()}")

    if args.comando == "criar":
        criar_usuario(args.username, args.senha, args.nome, args.perfil)
        print(f"Usuário '{args.username}' ({args.perfil}) criado com sucesso.")
    elif args.comando == "listar":
        df = query_df("SELECT id, username, nome, perfil, ativo, criado_em FROM usuarios ORDER BY id")
        print(df.to_string(index=False) if not df.empty else "Nenhum usuário cadastrado ainda.")


if __name__ == "__main__":
    main()
