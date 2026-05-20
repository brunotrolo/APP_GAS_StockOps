#!/usr/bin/env python3
"""OpLab MCP Server - Acesso em tempo real à API OpLab."""

import os
import json
import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = "https://api.oplab.com.br/v3"
ACCESS_TOKEN = os.environ.get("OPLAB_ACCESS_TOKEN", "")

mcp = FastMCP("OpLab")


def _headers() -> dict:
    return {"Access-Token": ACCESS_TOKEN}


def _fmt_quote(q: dict) -> str:
    lines = [f"## {q.get('symbol', '?')}"]
    if "close" in q:
        lines.append(f"- **Último preço**: R$ {q['close']:.2f}")
    if "variation" in q:
        lines.append(f"- **Variação**: {q['variation']:+.2f}%")
    if "bid" in q:
        lines.append(f"- **Compra (bid)**: R$ {q['bid']:.2f}")
    if "ask" in q:
        lines.append(f"- **Venda (ask)**: R$ {q['ask']:.2f}")
    if "open" in q:
        lines.append(f"- **Abertura**: R$ {q['open']:.2f}")
    if "high" in q:
        lines.append(f"- **Máxima**: R$ {q['high']:.2f}")
    if "low" in q:
        lines.append(f"- **Mínima**: R$ {q['low']:.2f}")
    if "volume" in q:
        lines.append(f"- **Volume**: {q['volume']:,.0f}")
    if "financial_volume" in q:
        lines.append(f"- **Volume financeiro**: R$ {q['financial_volume']:,.2f}")
    if "strike" in q and q["strike"]:
        lines.append(f"- **Strike**: R$ {q['strike']:.2f}")
    if "time" in q:
        import datetime
        ts = q["time"] / 1000
        dt = datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        lines.append(f"- **Horário**: {dt}")
    return "\n".join(lines)


@mcp.tool()
def get_quote(tickers: str) -> str:
    """
    Retorna cotação em tempo real de uma ou mais ações/opções da B3.

    Args:
        tickers: Código(s) do(s) ativo(s) separados por vírgula. Ex: "PETR4,VALE3" ou "PETRE100"
    """
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/market/quote",
            params={"tickers": tickers},
            headers=_headers(),
            timeout=10,
        )
    if resp.status_code == 204:
        return f"Nenhuma cotação encontrada para: {tickers}"
    if resp.status_code != 200:
        return f"Erro {resp.status_code}: {resp.text}"
    data = resp.json()
    if not data:
        return f"Nenhum dado retornado para: {tickers}"
    return "\n\n".join(_fmt_quote(q) for q in data)


@mcp.tool()
def get_instrument(symbol: str) -> str:
    """
    Retorna informações detalhadas de um instrumento (ação, opção, futuro, etc.) incluindo
    volatilidade implícita, gregas (delta, gamma, theta, vega), e dados fundamentais.

    Args:
        symbol: Código do ativo. Ex: "PETR4" ou "PETRE100"
    """
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/market/instruments/{symbol}",
            headers=_headers(),
            timeout=10,
        )
    if resp.status_code == 404:
        return f"Instrumento não encontrado: {symbol}"
    if resp.status_code != 200:
        return f"Erro {resp.status_code}: {resp.text}"
    data = resp.json()
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def search_instruments(query: str, type: str = "", limit: int = 10) -> str:
    """
    Busca instrumentos pelo nome ou código de negociação.

    Args:
        query: Texto de busca. Ex: "Petrobras" ou "PETR"
        type: Filtro de tipo: "STOCK", "OPTION", "FUND", "BDR", "FII", "INDEX", "FUTURE" (opcional)
        limit: Número máximo de resultados (padrão 10)
    """
    params: dict = {"expr": query, "limit": limit}
    if type:
        params["type"] = type
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/market/instruments/search",
            params=params,
            headers=_headers(),
            timeout=10,
        )
    if resp.status_code != 200:
        return f"Erro {resp.status_code}: {resp.text}"
    data = resp.json()
    if not data:
        return f"Nenhum instrumento encontrado para: {query}"
    lines = [f"**Resultados para '{query}':**\n"]
    for item in data:
        sym = item.get("symbol", "")
        name = item.get("name", item.get("company_name", ""))
        itype = item.get("type", "")
        lines.append(f"- `{sym}` — {name} ({itype})")
    return "\n".join(lines)


@mcp.tool()
def get_options_chain(symbol: str) -> str:
    """
    Retorna a cadeia de opções (série completa) de uma ação subjacente.
    Inclui calls e puts com preços, volatilidade implícita e gregas.

    Args:
        symbol: Código da ação-mãe. Ex: "PETR4", "VALE3", "IBOV"
    """
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/market/options/{symbol}",
            headers=_headers(),
            timeout=15,
        )
    if resp.status_code == 404:
        return f"Opções não encontradas para: {symbol}"
    if resp.status_code != 200:
        return f"Erro {resp.status_code}: {resp.text}"
    data = resp.json()
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def get_option_details(symbol: str) -> str:
    """
    Retorna detalhes completos de uma opção específica: preço teórico Black-Scholes,
    gregas (delta, gamma, theta, vega, rho), volatilidade implícita, e dados de mercado.

    Args:
        symbol: Código da opção. Ex: "PETRE100", "VALEF72"
    """
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/market/options/details/{symbol}",
            headers=_headers(),
            timeout=10,
        )
    if resp.status_code == 404:
        return f"Opção não encontrada: {symbol}"
    if resp.status_code != 200:
        return f"Erro {resp.status_code}: {resp.text}"
    data = resp.json()
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def get_market_status() -> str:
    """
    Retorna o status atual do mercado (aberto/fechado) e informações do pregão.
    """
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/market/status",
            headers=_headers(),
            timeout=10,
        )
    if resp.status_code != 200:
        return f"Erro {resp.status_code}: {resp.text}"
    data = resp.json()
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def get_covered_strategies(underlying: str) -> str:
    """
    Retorna estratégias de venda coberta (covered call) disponíveis para uma ação.

    Args:
        underlying: Código da ação-mãe. Ex: "PETR4", "VALE3"
    """
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/market/options/strategies/covered",
            params={"underlying": underlying},
            headers=_headers(),
            timeout=15,
        )
    if resp.status_code != 200:
        return f"Erro {resp.status_code}: {resp.text}"
    data = resp.json()
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def get_interest_rates() -> str:
    """
    Retorna as taxas de juros atuais (SELIC, CDI, etc.) utilizadas nos modelos de precificação.
    """
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/market/interest_rates",
            headers=_headers(),
            timeout=10,
        )
    if resp.status_code != 200:
        return f"Erro {resp.status_code}: {resp.text}"
    data = resp.json()
    return json.dumps(data, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if not ACCESS_TOKEN:
        print("ERRO: Defina a variável de ambiente OPLAB_ACCESS_TOKEN")
        exit(1)
    mcp.run(transport="stdio")
