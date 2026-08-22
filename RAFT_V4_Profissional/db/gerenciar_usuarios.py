import argparse
from auth import criar_usuario
from db_utils import query_df
p=argparse.ArgumentParser()
s=p.add_subparsers(dest="cmd",required=True)
c=s.add_parser("criar")
c.add_argument("--username",required=True); c.add_argument("--senha",required=True)
c.add_argument("--nome",required=True); c.add_argument("--perfil",required=True,
  choices=["OPERADOR","PCP","ALMOXARIFADO","ADMINISTRADOR"])
s.add_parser("listar")
a=p.parse_args()
if a.cmd=="criar":
    criar_usuario(a.username,a.senha,a.nome,a.perfil); print("Usuário criado.")
else:
    print(query_df("SELECT id,username,nome,perfil,ativo,criado_em,ultimo_login FROM usuarios").to_string(index=False))
