"""
VELUM Decision Engine — NegotiationDesk (MOCK / ILUSORIO)
===========================================================

ATENCAO: este arquivo é um substituto ilusório do motor real, criado
apenas para permitir testar o deploy do run_api.py (subida do servidor,
rotas, formato de resposta). Os numeros aqui NAO vem de um motor fiscal
de producao nem de hipoteses tributarias validadas — sao uma formula
simples e arbitraria so para gerar uma resposta plausivel.

Antes de usar isso com dados reais, troque este arquivo pelo
NegotiationDesk de verdade.
"""

import json
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent.parent / "rules.json"

# Divisao ilustrativa do impacto tributario entre fornecedor, gap e cliente.
# Numeros escolhidos so para exemplificar — sem base tecnica.
SPLIT_SUPPLIER = 0.44
SPLIT_GAP = 0.17
SPLIT_CLIENT = 0.39


class NegotiationDesk:
    """Versao ilusoria (mock) do NegotiationDesk. Apenas para teste de deploy."""

    def __init__(self, rules_path: Path = RULES_PATH):
        self.rules = {}
        if rules_path.exists():
            with open(rules_path, "r", encoding="utf-8") as f:
                self.rules = json.load(f)

    def _combined_rate(self, ano: str):
        """Retorna a aliquota combinada (IBS+CBS) ilustrativa do sandbox_rates,
        com fallback para a tabela 'transition' quando o ano nao esta no sandbox."""
        sandbox = self.rules.get("sandbox_rates", {})
        if ano in sandbox:
            ibs = sandbox[ano].get("ibs", 0)
            cbs = sandbox[ano].get("cbs", 0)
            return ibs + cbs

        transition = self.rules.get("transition", {})
        entry = transition.get(ano, {})
        ibs = entry.get("ibs_general_rate") or 0
        cbs = entry.get("cbs_rate") or 0
        return ibs + cbs

    def product(self, sku=None, custo_atual=None, preco_atual=None,
                margem_historica=None, volume_anual=None, ano="2029", **kwargs):
        """
        Calcula (de forma ilusoria) as ancoras de negociacao para um SKU.

        Parametros esperados (todos numericos, exceto sku/ano):
          sku, custo_atual, preco_atual, margem_historica (0-1), volume_anual, ano
        """
        sku = sku or "SKU-EXEMPLO"
        custo_atual = float(custo_atual or 100.0)
        preco_atual = float(preco_atual or custo_atual / (1 - float(margem_historica or 0.35)))
        margem_historica = float(margem_historica or 0.35)
        volume_anual = float(volume_anual or 1000)
        ano = str(ano)

        impacto_tributario = self._combined_rate(ano)  # ex.: 0.093 = 9,3%

        # Preco-alvo: preco que mantem a margem historica sobre o novo custo tributado
        custo_com_imposto = custo_atual * (1 + impacto_tributario)
        preco_alvo = custo_com_imposto / (1 - margem_historica)

        # Divisao ilustrativa do impacto entre fornecedor / gap / cliente
        reducao_fornecedor_pct = impacto_tributario * SPLIT_SUPPLIER
        gap_pct = impacto_tributario * SPLIT_GAP
        teto_reajuste_cliente_pct = impacto_tributario * SPLIT_CLIENT

        custo_maximo_fornecedor = custo_atual * (1 - reducao_fornecedor_pct)
        teto_preco_cliente = preco_atual * (1 + teto_reajuste_cliente_pct)

        impacto_anual_estimado = (preco_alvo - preco_atual) * volume_anual

        return {
            "status": "ok (mock)",
            "sku": sku,
            "ano": ano,
            "aliquota_combinada_estimada": round(impacto_tributario, 5),
            "preco_alvo": round(preco_alvo, 2),
            "custo_maximo_aceitavel_fornecedor": round(custo_maximo_fornecedor, 2),
            "percentual_reducao_fornecedor": round(reducao_fornecedor_pct, 5),
            "teto_reajuste_cliente_pct": round(teto_reajuste_cliente_pct, 5),
            "teto_preco_cliente": round(teto_preco_cliente, 2),
            "gap_a_dividir_pct": round(gap_pct, 5),
            "impacto_anual_estimado": round(impacto_anual_estimado, 2),
            "aviso": "Dados ilusorios (mock) — gerados apenas para teste de deploy, nao usar como referencia fiscal.",
        }

    def action_plan(self, result: dict):
        """Gera um plano de acao textual simples a partir do resultado calculado."""
        if not result or "sku" not in result:
            return []

        return [
            f"Abrir negociacao com o fornecedor pedindo reducao de "
            f"{result['percentual_reducao_fornecedor'] * 100:.1f}% sobre o custo atual do SKU {result['sku']}.",
            f"Nao repassar ao cliente mais que {result['teto_reajuste_cliente_pct'] * 100:.1f}% de reajuste "
            f"(teto de preco: R$ {result['teto_preco_cliente']:.2f}).",
            f"Reservar {result['gap_a_dividir_pct'] * 100:.1f} p.p. como gap a dividir internamente, "
            f"caso fornecedor e cliente nao cubram o impacto total.",
            f"Impacto anual estimado se nada mudar: R$ {result['impacto_anual_estimado']:.2f}.",
        ]
