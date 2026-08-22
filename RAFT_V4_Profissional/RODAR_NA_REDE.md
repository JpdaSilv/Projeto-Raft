# Rodar o RAFT V4 na rede local

## 1. No computador servidor

Abra o terminal nesta pasta e instale as dependencias:

```bash
pip install -r requirements.txt
```

Depois execute:

```bash
python -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

Ou, no Windows, dê dois cliques em `rodar_rede.bat`.

## 2. Descobrir o IP do computador servidor

No Prompt de Comando:

```cmd
ipconfig
```

Procure o `Endereço IPv4`, por exemplo:

```text
192.168.1.50
```

## 3. Abrir em outro computador/celular da mesma rede

No navegador:

```text
http://192.168.1.50:8501
```

Troque `192.168.1.50` pelo IPv4 real do computador servidor.

## 4. Firewall do Windows

Se outro dispositivo não conseguir abrir, permita a porta TCP 8501 no Firewall do Windows ou permita o Python/Streamlit quando o Windows solicitar.

## 5. Arquitetura recomendada

```text
PC SERVIDOR
    |
    |-- Streamlit :8501
    |-- SQLite (banco/raft_app.db)
    |
    +---- Rede local ---- PC 2
    +---- Rede local ---- PC 3
    +---- Rede local ---- Celular/Tablet
```

Todos os usuários acessam a mesma aplicação no computador servidor. O SQLite permanece somente no servidor.

**Não coloque o arquivo `.db` em uma pasta de rede compartilhada para vários computadores acessarem diretamente.** O Streamlit deve ser o intermediário.

## Segurança

Essa configuração é para **rede local confiável**. Não exponha a porta 8501 diretamente à internet. Para acesso externo, use VPN ou uma arquitetura de hospedagem adequada.
