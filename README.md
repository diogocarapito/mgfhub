# mgfhub

[![Github Actions Workflow](https://github.com/DiogoCarapito/mgfhub/actions/workflows/main.yaml/badge.svg)](https://github.com/DiogoCarapito/mgfhub/actions/workflows/main.yaml)

Ferramenta de pesquisa e análise de indicadores dos Cuidados de Saúde Primarios portugueses

Funcionalidades:

- pesquisa por palavras chave da descrição ou número do indicador
- filtrar por indicadores do IDE, IDG ou todos
- visualização em tabela ou cartões
- Relatórios de analise de desempenho da unidade, equipas e por profissional, com filtros e analise de evolução temporal

Nova versão 2.1 disponível em [mgfhub.com](mgfhub.com)

---

## Desenvolvimento local

```bash
make venv    # primeira vez: cria .venv (python3.13) e instala dependências
make run     # corre a app em http://localhost:8501
make test    # corre os testes
make check   # format + lint + testes (antes de cada commit)
make help    # lista todos os comandos
```

Os targets do Makefile usam `.venv/bin/` automaticamente — não é preciso ativar o venv.

### Docker

```bash
make docker  # build + run + health-check + stop
```

ou manualmente com `make docker-build` / `make docker-run` / `make docker-test`.

docker scout:

```bash
docker scout quickview mgfhub:latest
docker scout cves mgfhub:latest
docker scout recommendations mgfhub:latest
```