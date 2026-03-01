"""
RELATORIO EXECUTIVO DIARIO DE INVESTIMENTOS
Powered by Gemini (Google AI) + Google Search
Entrega via WhatsApp (CallMeBot)

Fontes de referencia: Reuters, Bloomberg, Valor Economico, BCB, IBGE, B3, CoinGecko
AVISO: Apenas educacional. Nao constitui recomendacao de investimento.
"""

import requests
import os
from datetime import datetime, timezone, timedelta

# ================================================================
# CONFIGURACOES - valores vem dos Secrets do GitHub
# ================================================================
CALLMEBOT_PHONE  = os.environ.get("CALLMEBOT_PHONE",  "SEU_NUMERO")
CALLMEBOT_APIKEY = os.environ.get("CALLMEBOT_APIKEY", "SUA_CHAVE")
GEMINI_APIKEY    = os.environ.get("GEMINI_API_KEY",   "SUA_CHAVE_GEMINI")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-1.5-flash:generateContent?key=" + (os.environ.get("GEMINI_API_KEY", ""))
)

# ================================================================
# WHATSAPP
# ================================================================
def enviar_whatsapp(mensagem, parte=1, total=1):
    blocos = [mensagem[i:i+1400] for i in range(0, len(mensagem), 1400)]
    for i, bloco in enumerate(blocos):
        url = (
            "https://api.callmebot.com/whatsapp.php"
            "?phone=" + CALLMEBOT_PHONE +
            "&text=" + requests.utils.quote(bloco) +
            "&apikey=" + CALLMEBOT_APIKEY
        )
        try:
            r = requests.get(url, timeout=15)
            print(f"  WhatsApp {parte}/{total} bloco {i+1} [{r.status_code}]")
        except Exception as e:
            print(f"  Erro WhatsApp: {e}")

# ================================================================
# PROMPT DO RELATORIO
# ================================================================
def construir_prompt(data):
    return (
        "Voce e um analista financeiro senior de uma gestora de investimentos brasileira.\n\n"
        "Data de hoje: " + data + "\n\n"
        "Sua tarefa: gerar um RELATORIO EXECUTIVO DIARIO DE INVESTIMENTOS baseado nas "
        "principais noticias economicas e financeiras publicadas nas ULTIMAS 24 HORAS.\n\n"
        "Fontes de referencia obrigatorias: Reuters, Bloomberg, Financial Times, "
        "Valor Economico, InfoMoney, Agencia Brasil, Banco Central do Brasil, "
        "IBGE, CVM, B3, CoinGecko.\n\n"
        "Gere o relatorio com EXATAMENTE esta estrutura:\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *RELATORIO EXECUTIVO DIARIO*\n"
        "📅 " + data + "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📌 *RESUMO EXECUTIVO*\n"
        "[2-3 frases: tom do mercado (risk-on ou risk-off), principais drivers do dia]\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🌍 *CENARIO GLOBAL*\n"
        "[3-4 pontos com numeros especificos: postura Fed/BCE, dados economicos "
        "divulgados (CPI/PMI/Payroll/PIB), geopolitica com impacto nos mercados, "
        "commodities: petroleo, ouro, minerio de ferro]\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🇧🇷 *CENARIO BRASIL*\n"
        "[3-4 pontos com numeros: Selic e expectativas Copom, resultado fiscal, "
        "IPCA/IGP-M, cambio dolar/real e fatores de pressao, eventos politicos "
        "com impacto economico]\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📈 *MERCADO DE ACOES*\n"
        "[Ibovespa: pontos e variacao %. S&P 500, Nasdaq, Dow Jones: variacao. "
        "Setores em destaque positivo e negativo na B3. "
        "Acoes individuais com movimentos relevantes. Fluxo estrangeiro]\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "₿ *MERCADO CRIPTO*\n"
        "[Bitcoin: preco e variacao 24h. Ethereum e altcoins. "
        "Dominancia BTC. ETFs spot. Regulacao. Fear and Greed Index]\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔦 *RADAR DO DIA*\n"
        "[3 eventos/dados com maior impacto esperado:]\n\n"
        "1️⃣ [Nome do evento]\n"
        "   Impacto: [Por que importa para os mercados]\n\n"
        "2️⃣ [Nome do evento]\n"
        "   Impacto: [Por que importa para os mercados]\n\n"
        "3️⃣ [Nome do evento]\n"
        "   Impacto: [Por que importa para os mercados]\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🧭 *DIRECIONAMENTO ESTRATEGICO*\n"
        "[3-4 observacoes tecnicas sobre alocacao de portfolio. "
        "NUNCA use as palavras compre, venda, aplique ou resgate. "
        "Use: 'o ambiente favorece...', 'o cenario sugere atencao a...', "
        "'historicamente neste contexto...', 'investidores tendem a buscar...']\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ *AVISO*\n"
        "Este relatorio tem carater exclusivamente educacional e informativo. "
        "Nao constitui recomendacao de investimento. "
        "Consulte um profissional habilitado antes de tomar decisoes financeiras.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 Fontes: Reuters · Bloomberg · Valor Economico · BCB · B3\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "REGRAS OBRIGATORIAS:\n"
        "- Use APENAS informacoes das ultimas 24 horas\n"
        "- Se nao houver dado, escreva 'dado nao disponivel'\n"
        "- Nunca use compre, venda, aplique ou recomendacao personalizada\n"
        "- Maximo 2800 caracteres no total\n"
        "- Seja tecnico, claro e objetivo\n"
    )

# ================================================================
# GERACAO DO RELATORIO (com fallback automatico)
# ================================================================
def gerar_relatorio(data):
    prompt = construir_prompt(data)
    gemini_url = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        "/gemini-1.5-flash:generateContent?key=" + GEMINI_APIKEY
    )

    # Tentativa 1: com Google Search (noticias em tempo real)
    print("  Tentando com Google Search (tempo real)...")
    try:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"maxOutputTokens": 2048, "temperature": 0.2},
        }
        r = requests.post(gemini_url, json=payload, timeout=90)
        if r.status_code == 200:
            texto = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            print("  OK - relatorio gerado com noticias em tempo real")
            return texto
        print(f"  Google Search retornou {r.status_code} - usando fallback")
    except Exception as e:
        print(f"  Erro Google Search: {e} - usando fallback")

    # Tentativa 2: sem grounding
    print("  Gerando sem busca em tempo real...")
    try:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 2048, "temperature": 0.2},
        }
        r = requests.post(gemini_url, json=payload, timeout=90)
        r.raise_for_status()
        texto = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        nota  = (
            "\n\n_Nota: relatorio gerado sem acesso em tempo real. "
            "Dados podem nao refletir os eventos das ultimas 24h._"
        )
        print("  OK - relatorio gerado sem tempo real")
        return texto + nota
    except Exception as e:
        return f"ERRO: {e}"

# ================================================================
# DIVISAO EM BLOCOS PARA WHATSAPP
# ================================================================
def dividir(texto):
    SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    MAX = 1400
    partes = texto.split(SEP)
    msgs, buf = [], ""
    for p in partes:
        p = p.strip()
        if not p:
            continue
        trecho = ("\n\n" + SEP + "\n\n" + p) if buf else p
        if len(buf) + len(trecho) <= MAX:
            buf += trecho
        else:
            if buf:
                msgs.append(buf.strip())
            buf = p
    if buf.strip():
        msgs.append(buf.strip())
    return msgs if msgs else [texto]

# ================================================================
# EXECUCAO PRINCIPAL
# ================================================================
def rodar():
    tz    = timezone(timedelta(hours=-3))
    agora = datetime.now(tz)
    data  = agora.strftime("%d/%m/%Y")
    hora  = agora.strftime("%H:%M")

    print("\n" + "="*65)
    print(f"  RELATORIO EXECUTIVO - {data} {hora} (Brasilia)")
    print("="*65 + "\n")

    print("Gerando relatorio com Gemini...")
    relatorio = gerar_relatorio(data)

    if relatorio.startswith("ERRO"):
        print(relatorio)
        enviar_whatsapp(
            f"Falha no Relatorio Diario\n"
            f"Data: {data} {hora}\n"
            f"{relatorio}"
        )
        return

    print(f"Relatorio gerado: {len(relatorio)} caracteres")
    msgs  = dividir(relatorio)
    total = len(msgs)
    print(f"Enviando {total} mensagem(ns) no WhatsApp...")

    for i, msg in enumerate(msgs, 1):
        if total > 1:
            msg = f"Parte {i}/{total}\n\n{msg}"
        enviar_whatsapp(msg, i, total)

    print(f"Concluido: {agora.strftime('%H:%M:%S')} (Brasilia)")

if __name__ == "__main__":
    rodar()
