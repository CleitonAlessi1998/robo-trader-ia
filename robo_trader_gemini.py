"""
╔══════════════════════════════════════════════════════════════════╗
║       ROBÔ TRADER PRO — Metodologia Profissional                 ║
║              IA: Google Gemini (gratuito)                        ║
║                                                                  ║
║  ✅ Tendência semanal: Topos+Fundos + MMs (9, 21, 50)            ║
║  ✅ Pull back no diário identificado                             ║
║  ✅ Stop técnico: fundo relevante dos últimos 20 dias            ║
║  ✅ Alvo: próxima resistência relevante (topo anterior)          ║
║  ✅ R:R mínimo 3:1 obrigatório para validar o setup              ║
║  ✅ Volume confirmando o movimento                               ║
║  ✅ Expectativa matemática positiva calculada                    ║
║  ✅ Análise completa pelo Gemini (IA gratuita) em português      ║
║  ✅ Alertas via WhatsApp (CallMeBot, gratuito)                   ║
╚══════════════════════════════════════════════════════════════════╝

AVISO: Apenas educacional. Não é recomendação de investimento.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime

# ════════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURAÇÕES
# ════════════════════════════════════════════════════════════════

CALLMEBOT_PHONE   = os.environ.get("CALLMEBOT_PHONE",   "5542999055775")
CALLMEBOT_APIKEY  = os.environ.get("CALLMEBOT_APIKEY",  "1109879")
GEMINI_APIKEY     = os.environ.get("GEMINI_API_KEY", "AIzaSyAATpIJc9nHXHYwC_XoxNKijuhkPp0p3UM")

ATIVOS = {
    "Ações BR": [
        {"ticker": "PETR4.SA", "nome": "Petrobras"},
        {"ticker": "VALE3.SA", "nome": "Vale"},
        {"ticker": "ITUB4.SA", "nome": "Itaú"},
        {"ticker": "BBDC4.SA", "nome": "Bradesco"},
        {"ticker": "MGLU3.SA", "nome": "Magazine Luiza"},
    ],
    "Cripto": [
        {"ticker": "BTC-USD",  "nome": "Bitcoin"},
        {"ticker": "ETH-USD",  "nome": "Ethereum"},
        {"ticker": "BNB-USD",  "nome": "BNB"},
    ],
    "Dólar": [
        {"ticker": "BRL=X",    "nome": "Dólar Comercial"},
    ],
}

# Parâmetros da metodologia
RR_MINIMO          = 3.0    # R:R mínimo para validar o setup
JANELA_STOP        = 20     # Dias para buscar o fundo relevante (stop)
JANELA_ALVO        = 60     # Dias para buscar a resistência relevante (alvo)
PULLBACK_RSI_MAX   = 50     # RSI máximo para confirmar que é pullback (não rompimento)
PULLBACK_RSI_MIN   = 30     # RSI mínimo (abaixo = sobrevendido demais, pode não ser pullback)
VOL_CONFIRMACAO    = 0.8    # Volume do pullback deve ser < 80% da média (seco = bom sinal)
VOL_TENDENCIA_MIN  = 1.2    # Volume na tendência deve ser > 120% da média (força)

# Médias móveis para tendência
MM_CURTA   = 9
MM_MEDIA   = 21
MM_LONGA   = 50

# ════════════════════════════════════════════════════════════════
#  📡  UTILITÁRIOS
# ════════════════════════════════════════════════════════════════

def enviar_whatsapp(mensagem: str):
    max_len = 1500
    partes = [mensagem[i:i+max_len] for i in range(0, len(mensagem), max_len)]
    for parte in partes:
        url = (
            f"https://api.callmebot.com/whatsapp.php"
            f"?phone={CALLMEBOT_PHONE}"
            f"&text={requests.utils.quote(parte)}"
            f"&apikey={CALLMEBOT_APIKEY}"
        )
        try:
            r = requests.get(url, timeout=15)
            print(f"  WhatsApp [{r.status_code}]")
        except Exception as e:
            print(f"  Erro WhatsApp: {e}")


def calcular_rsi(series: pd.Series, periodo: int = 14) -> float:
    delta = series.diff()
    ganho = delta.clip(lower=0).rolling(periodo).mean()
    perda = (-delta.clip(upper=0)).rolling(periodo).mean()
    rs = ganho / perda
    return round(float((100 - (100 / (1 + rs))).iloc[-1]), 2)


def safe_float(val) -> float:
    """Converte qualquer valor numérico pandas/numpy para float puro."""
    try:
        return float(np.ravel(val)[0])
    except Exception:
        return float(val)


# ════════════════════════════════════════════════════════════════
#  📊  ANÁLISE DE TENDÊNCIA SEMANAL
#  Critério: Topos e fundos ascendentes/descendentes + MMs alinhadas
# ════════════════════════════════════════════════════════════════

def analisar_tendencia_semanal(ticker: str) -> dict:
    """
    Baixa dados semanais e verifica:
    1. Sequência de topos e fundos (estrutura de mercado)
    2. MMs 9, 21, 50 semanas alinhadas (9 > 21 > 50 = alta / 9 < 21 < 50 = baixa)
    Retorna: tendencia ("ALTA" | "BAIXA" | "INDEFINIDA"), score e detalhes
    """
    try:
        df = yf.download(ticker, period="2y", interval="1wk", progress=False)
        if df.empty or len(df) < 55:
            return {"tendencia": "INDEFINIDA", "score": 0, "detalhes": "Dados insuficientes"}

        close = df["Close"].squeeze()
        high  = df["High"].squeeze()
        low   = df["Low"].squeeze()

        # ── MMs semanais ──────────────────────────────────────
        mm9  = safe_float(close.rolling(MM_CURTA).mean().iloc[-1])
        mm21 = safe_float(close.rolling(MM_MEDIA).mean().iloc[-1])
        mm50 = safe_float(close.rolling(MM_LONGA).mean().iloc[-1])
        preco_atual = safe_float(close.iloc[-1])

        mm_altista  = mm9 > mm21 > mm50 and preco_atual > mm9
        mm_baixista = mm9 < mm21 < mm50 and preco_atual < mm9
        mm_score = 2 if mm_altista else (-2 if mm_baixista else 0)

        # ── Topos e fundos (últimas 12 semanas, janela de 3) ──
        janela = 3
        topos  = []
        fundos = []
        highs = high.values
        lows  = low.values

        for i in range(janela, len(highs) - janela):
            if highs[i] == max(highs[i-janela:i+janela+1]):
                topos.append(highs[i])
            if lows[i] == min(lows[i-janela:i+janela+1]):
                fundos.append(lows[i])

        # Pega últimos 3 topos e fundos relevantes
        topos  = topos[-3:]  if len(topos)  >= 2 else []
        fundos = fundos[-3:] if len(fundos) >= 2 else []

        topos_asc  = len(topos)  >= 2 and all(topos[i]  < topos[i+1]  for i in range(len(topos)-1))
        topos_desc = len(topos)  >= 2 and all(topos[i]  > topos[i+1]  for i in range(len(topos)-1))
        fundos_asc = len(fundos) >= 2 and all(fundos[i] < fundos[i+1] for i in range(len(fundos)-1))
        fundos_desc= len(fundos) >= 2 and all(fundos[i] > fundos[i+1] for i in range(len(fundos)-1))

        tf_score = 0
        if topos_asc  and fundos_asc:  tf_score =  2   # tendência de alta confirmada
        if topos_desc and fundos_desc: tf_score = -2   # tendência de baixa confirmada
        if topos_asc  and not fundos_asc:  tf_score =  1
        if topos_desc and not fundos_desc: tf_score = -1

        score_total = mm_score + tf_score  # -4 a +4

        if score_total >= 3:
            tendencia = "ALTA"
        elif score_total <= -3:
            tendencia = "BAIXA"
        else:
            tendencia = "INDEFINIDA"

        detalhes = (
            f"MM9={mm9:.2f} MM21={mm21:.2f} MM50={mm50:.2f} | "
            f"Topos {'↑' if topos_asc else ('↓' if topos_desc else '~')} "
            f"Fundos {'↑' if fundos_asc else ('↓' if fundos_desc else '~')} | "
            f"Score={score_total}/4"
        )

        return {
            "tendencia": tendencia,
            "score":     score_total,
            "mm9_sem":   round(mm9, 4),
            "mm21_sem":  round(mm21, 4),
            "mm50_sem":  round(mm50, 4),
            "topos_asc": topos_asc,
            "fundos_asc":fundos_asc,
            "detalhes":  detalhes,
        }

    except Exception as e:
        return {"tendencia": "INDEFINIDA", "score": 0, "detalhes": str(e)}


# ════════════════════════════════════════════════════════════════
#  📉  IDENTIFICAÇÃO DE PULL BACK NO DIÁRIO
#  Pullback = retração em tendência de alta com volume seco
# ════════════════════════════════════════════════════════════════

def identificar_pullback(df_diario: pd.DataFrame, tendencia: str) -> dict:
    """
    Num ativo em tendência de alta, pullback é:
    - RSI entre 30 e 50 (retração, não colapso)
    - Preço afastou das máximas recentes (pelo menos 2%)
    - Volume abaixo da média nos últimos 3 dias (volume seco = fraqueza dos vendedores)
    - Preço ainda acima da MM21 diária (estrutura intacta)
    """
    try:
        close = df_diario["Close"].squeeze()
        vol   = df_diario["Volume"].squeeze()

        preco    = safe_float(close.iloc[-1])
        mm9d     = safe_float(close.rolling(9).mean().iloc[-1])
        mm21d    = safe_float(close.rolling(21).mean().iloc[-1])
        rsi      = calcular_rsi(close)

        max_20d  = safe_float(close.tail(20).max())
        vol_med  = safe_float(vol.rolling(20).mean().iloc[-1])
        vol_3d   = safe_float(vol.tail(3).mean())
        vol_rel  = round(vol_3d / vol_med, 2) if vol_med > 0 else 1.0

        afastamento_max = round((max_20d - preco) / max_20d * 100, 2) if max_20d > 0 else 0

        # Critérios para confirmar pullback em tendência de alta
        if tendencia == "ALTA":
            criterios = {
                "rsi_em_zona":        PULLBACK_RSI_MIN <= rsi <= PULLBACK_RSI_MAX,
                "afastou_da_maxima":  afastamento_max >= 2.0,
                "volume_seco":        vol_rel <= VOL_CONFIRMACAO,
                "acima_mm21":         preco > mm21d,
                "acima_mm9":          preco > mm9d or preco > mm21d,  # flexível
            }
            criterios_ok = sum(criterios.values())
            e_pullback = criterios_ok >= 4  # pelo menos 4 dos 5 critérios

        elif tendencia == "BAIXA":
            # Pullback de baixa = repique fraco com volume seco
            criterios = {
                "rsi_em_zona":        50 <= rsi <= 70,
                "afastou_da_minima":  True,  # simplificado
                "volume_seco":        vol_rel <= VOL_CONFIRMACAO,
                "abaixo_mm21":        preco < mm21d,
                "abaixo_mm9":         preco < mm9d,
            }
            criterios_ok = sum(criterios.values())
            e_pullback = criterios_ok >= 4
        else:
            criterios    = {}
            criterios_ok = 0
            e_pullback   = False

        return {
            "e_pullback":      e_pullback,
            "rsi_diario":      rsi,
            "vol_relativo":    vol_rel,
            "afastamento_max": afastamento_max,
            "mm9d":            round(mm9d, 4),
            "mm21d":           round(mm21d, 4),
            "criterios_ok":    criterios_ok,
            "criterios":       criterios,
        }

    except Exception as e:
        return {"e_pullback": False, "rsi_diario": 0, "vol_relativo": 1, "afastamento_max": 0,
                "mm9d": 0, "mm21d": 0, "criterios_ok": 0, "criterios": {}}


# ════════════════════════════════════════════════════════════════
#  🛑  STOP TÉCNICO — Fundo relevante dos últimos 20 dias
# ════════════════════════════════════════════════════════════════

def calcular_stop_tecnico(df_diario: pd.DataFrame) -> dict:
    """
    Busca o fundo mais relevante nos últimos 20 dias.
    Fundo relevante = candle cuja mínima é menor que os 2 candles anteriores e 2 posteriores.
    Se não encontrar, usa a mínima absoluta dos últimos 20 dias com buffer de 0.5%.
    """
    try:
        low   = df_diario["Low"].squeeze().tail(JANELA_STOP).values
        close = df_diario["Close"].squeeze()
        preco = safe_float(close.iloc[-1])

        # Busca fundos relevantes (pivot lows)
        fundos_relevantes = []
        for i in range(2, len(low) - 2):
            if low[i] < low[i-1] and low[i] < low[i-2] and \
               low[i] < low[i+1] and low[i] < low[i+2]:
                fundos_relevantes.append(low[i])

        if fundos_relevantes:
            # Pega o fundo mais recente (último da lista = mais próximo do preço atual)
            stop_base = fundos_relevantes[-1]
            metodo = "Fundo relevante (pivot)"
        else:
            # Fallback: mínima absoluta dos últimos 20 dias
            stop_base = float(np.min(low))
            metodo = "Mínima absoluta 20d"

        # Buffer de segurança abaixo do fundo (0.5%)
        stop = round(stop_base * 0.995, 4)
        risco_pct = round((preco - stop) / preco * 100, 2)

        return {
            "stop":      stop,
            "risco_pct": risco_pct,          # % de risco do preço atual até o stop
            "metodo":    metodo,
        }

    except Exception as e:
        return {"stop": 0, "risco_pct": 0, "metodo": str(e)}


# ════════════════════════════════════════════════════════════════
#  🎯  ALVO — Próxima resistência relevante (topo anterior)
# ════════════════════════════════════════════════════════════════

def calcular_alvo(df_diario: pd.DataFrame) -> dict:
    """
    Busca topos relevantes nos últimos JANELA_ALVO dias.
    O alvo é o primeiro topo relevante ACIMA do preço atual.
    """
    try:
        high  = df_diario["High"].squeeze().tail(JANELA_ALVO)
        close = df_diario["Close"].squeeze()
        preco = safe_float(close.iloc[-1])
        high_vals = high.values

        # Busca topos relevantes (pivot highs)
        topos = []
        for i in range(2, len(high_vals) - 2):
            if high_vals[i] > high_vals[i-1] and high_vals[i] > high_vals[i-2] and \
               high_vals[i] > high_vals[i+1] and high_vals[i] > high_vals[i+2]:
                topos.append(high_vals[i])

        # Filtra apenas topos acima do preço atual
        topos_acima = sorted([t for t in topos if t > preco * 1.005])

        if topos_acima:
            alvo = round(topos_acima[0], 4)
            metodo = "Topo anterior (resistência)"
        else:
            # Fallback: máxima dos últimos 60 dias
            alvo = round(safe_float(high.max()), 4)
            metodo = "Máxima 60d (sem topo identificado)"

        potencial_pct = round((alvo - preco) / preco * 100, 2)

        return {
            "alvo":          alvo,
            "potencial_pct": potencial_pct,  # % de ganho potencial
            "metodo":        metodo,
            "qtd_topos":     len(topos_acima),
        }

    except Exception as e:
        return {"alvo": 0, "potencial_pct": 0, "metodo": str(e), "qtd_topos": 0}


# ════════════════════════════════════════════════════════════════
#  📐  R:R e EXPECTATIVA MATEMÁTICA
# ════════════════════════════════════════════════════════════════

def calcular_rr_e_expectativa(preco: float, stop: float, alvo: float) -> dict:
    """
    R:R = Potencial de ganho / Risco
    Expectativa matemática = (taxa_acerto × ganho_médio) - (taxa_erro × perda_média)
    Usamos taxa de acerto conservadora de 40% para swing trade.
    """
    try:
        risco   = preco - stop
        retorno = alvo  - preco

        if risco <= 0 or retorno <= 0:
            return {"rr": 0, "valido": False, "expectativa": 0, "risco_unit": 0, "retorno_unit": 0}

        rr = round(retorno / risco, 2)

        # Expectativa positiva com taxa de acerto conservadora (40%)
        taxa_acerto = 0.40
        taxa_erro   = 1 - taxa_acerto
        expectativa = round((taxa_acerto * retorno) - (taxa_erro * risco), 4)
        expectativa_pct = round(expectativa / preco * 100, 2)

        return {
            "rr":               rr,
            "valido":           rr >= RR_MINIMO,
            "risco_unit":       round(risco, 4),
            "retorno_unit":     round(retorno, 4),
            "expectativa":      expectativa,
            "expectativa_pct":  expectativa_pct,
            "expectativa_pos":  expectativa > 0,
        }

    except Exception as e:
        return {"rr": 0, "valido": False, "expectativa": 0, "risco_unit": 0, "retorno_unit": 0}


# ════════════════════════════════════════════════════════════════
#  🔬  ANÁLISE COMPLETA DE UM ATIVO
# ════════════════════════════════════════════════════════════════

def analisar_ativo_completo(ticker: str, nome: str) -> dict | None:
    """
    Orquestra toda a análise profissional:
    1. Tendência no semanal
    2. Pullback no diário
    3. Stop técnico (fundo relevante 20d)
    4. Alvo (resistência relevante)
    5. R:R ≥ 3:1
    6. Expectativa positiva
    """
    print(f"  Analisando {nome} ({ticker})...")
    try:
        # Dados diários (90 dias para ter contexto suficiente)
        df_d = yf.download(ticker, period="120d", interval="1d", progress=False)
        if df_d.empty or len(df_d) < 30:
            print(f"    ⚠️  Dados diários insuficientes")
            return None

        close  = df_d["Close"].squeeze()
        vol    = df_d["Volume"].squeeze()
        preco  = safe_float(close.iloc[-1])
        var_1d = round(float((close.iloc[-1] / close.iloc[-2] - 1) * 100), 2)
        var_5d = round(float((close.iloc[-1] / close.iloc[-6] - 1) * 100), 2) if len(close) > 6 else 0

        # ── 1. Tendência semanal ──────────────────────────────
        sem = analisar_tendencia_semanal(ticker)

        # ── 2. Pullback diário ────────────────────────────────
        pb  = identificar_pullback(df_d, sem["tendencia"])

        # ── 3. Stop técnico ───────────────────────────────────
        st  = calcular_stop_tecnico(df_d)

        # ── 4. Alvo ───────────────────────────────────────────
        av  = calcular_alvo(df_d)

        # ── 5. R:R e Expectativa ──────────────────────────────
        rr  = calcular_rr_e_expectativa(preco, st["stop"], av["alvo"])

        # ── 6. Volume (confirmação de tendência) ──────────────
        vol_med_20  = safe_float(vol.rolling(20).mean().iloc[-1])
        vol_hoje    = safe_float(vol.iloc[-1])
        vol_rel_hoje= round(vol_hoje / vol_med_20, 2) if vol_med_20 > 0 else 1.0

        # ── VEREDICTO FINAL ───────────────────────────────────
        # Setup válido SOMENTE se TODOS os critérios forem atendidos
        criterios_setup = {
            "tendencia_definida":    sem["tendencia"] in ("ALTA", "BAIXA"),
            "pullback_identificado": pb["e_pullback"],
            "rr_minimo_atingido":    rr["valido"],
            "expectativa_positiva":  rr["expectativa_pos"],
            "stop_definido":         st["stop"] > 0,
            "alvo_definido":         av["alvo"] > 0,
        }

        setup_valido    = all(criterios_setup.values())
        criterios_count = sum(criterios_setup.values())

        # Direção do setup
        if setup_valido:
            direcao = "COMPRA" if sem["tendencia"] == "ALTA" else "VENDA"
        else:
            direcao = "AGUARDAR"

        print(f"    → Tendência: {sem['tendencia']} | Pullback: {pb['e_pullback']} | "
              f"R:R: {rr['rr']} | Setup: {'✅' if setup_valido else '❌'}")

        return {
            # Identificação
            "ticker":   ticker,
            "nome":     nome,
            "preco":    preco,
            "var_1d":   var_1d,
            "var_5d":   var_5d,

            # Tendência semanal
            "tendencia":      sem["tendencia"],
            "tendencia_score":sem["score"],
            "mm9_sem":        sem.get("mm9_sem", 0),
            "mm21_sem":       sem.get("mm21_sem", 0),
            "mm50_sem":       sem.get("mm50_sem", 0),
            "topos_asc":      sem.get("topos_asc", False),
            "fundos_asc":     sem.get("fundos_asc", False),

            # Pullback diário
            "e_pullback":      pb["e_pullback"],
            "rsi_diario":      pb["rsi_diario"],
            "vol_pullback":    pb["vol_relativo"],
            "afastamento_max": pb["afastamento_max"],
            "mm9d":            pb["mm9d"],
            "mm21d":           pb["mm21d"],
            "pb_criterios_ok": pb["criterios_ok"],

            # Stop e Alvo
            "stop":        st["stop"],
            "risco_pct":   st["risco_pct"],
            "stop_metodo": st["metodo"],
            "alvo":        av["alvo"],
            "potencial_pct": av["potencial_pct"],
            "alvo_metodo": av["metodo"],

            # R:R e Expectativa
            "rr":              rr["rr"],
            "rr_valido":       rr["valido"],
            "expectativa_pct": rr["expectativa_pct"],
            "expectativa_pos": rr["expectativa_pos"],

            # Volume
            "vol_relativo": vol_rel_hoje,

            # Resultado final
            "setup_valido":      setup_valido,
            "criterios_count":   criterios_count,
            "criterios_setup":   criterios_setup,
            "direcao":           direcao,
        }

    except Exception as e:
        print(f"    ❌ Erro em {ticker}: {e}")
        return None


# ════════════════════════════════════════════════════════════════
#  🤖  ANÁLISE COM CLAUDE (IA)
# ════════════════════════════════════════════════════════════════

def analisar_com_gemini(todos_dados: list, setups_validos: list) -> str:
    """
    Envia os dados técnicos para o Google Gemini (gratuito)
    e retorna a análise completa em português.

    Modelo usado: gemini-1.5-flash (gratuito, generoso em requisições)
    Limites gratuitos: 15 req/min, 1.500 req/dia, 1M tokens/min
    """
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Monta contexto técnico completo
    resumo_todos = []
    for d in todos_dados:
        resumo_todos.append(
            f"• {d['nome']} ({d['ticker']}): Preço={d['preco']} | "
            f"Tendência={d['tendencia']} (score {d['tendencia_score']}/4) | "
            f"Pullback={'Sim' if d['e_pullback'] else 'Não'} | "
            f"RSI={d['rsi_diario']} | R:R={d['rr']} | "
            f"Stop={d['stop']} ({d['risco_pct']}% risco) | "
            f"Alvo={d['alvo']} ({d['potencial_pct']}% potencial) | "
            f"Expectativa={d['expectativa_pct']}% | "
            f"Vol relativo={d['vol_relativo']}x | "
            f"Setup válido={'✅ SIM' if d['setup_valido'] else '❌ NÃO'} ({d['criterios_count']}/6 critérios)"
        )

    resumo_setups = []
    for d in setups_validos:
        criterios_str = ", ".join(
            f"{k}={'✅' if v else '❌'}"
            for k, v in d["criterios_setup"].items()
        )
        resumo_setups.append(
            f"• {d['nome']} ({d['ticker']}) — {d['direcao']}\n"
            f"  Entrada: {d['preco']} | Stop: {d['stop']} | Alvo: {d['alvo']}\n"
            f"  R:R={d['rr']} | Expectativa={d['expectativa_pct']}% | "
            f"Critérios: {criterios_str}"
        )

    prompt = f"""Você é um analista de swing trade profissional, com foco em operações de 5 a 20 dias.
Data/hora atual: {agora}

Recebi os resultados do robô de análise técnica com a metodologia:
- Tendência semanal: topos+fundos + MMs (9, 21, 50 semanas)
- Pullback no diário identificado algoritmicamente
- Stop técnico: fundo relevante dos últimos 20 dias
- Alvo: próxima resistência relevante (topo anterior)
- R:R mínimo 3:1
- Expectativa matemática positiva (taxa de acerto conservadora de 40%)

━━ TODOS OS ATIVOS ANALISADOS ━━
{chr(10).join(resumo_todos)}

━━ SETUPS VÁLIDOS (TODOS OS CRITÉRIOS ATENDIDOS) ━━
{chr(10).join(resumo_setups) if resumo_setups else "Nenhum setup válido encontrado neste momento."}

Por favor, faça uma análise em PORTUGUÊS com:

1. 🧭 CONTEXTO MACRO: Sentimento atual do mercado (juros, dólar, commodities, cripto global) que impacta esses ativos.

2. 📊 SETUPS VÁLIDOS: Para cada setup válido, explique em linguagem clara: por que está em pullback, onde está o suporte, qual a lógica do alvo, e se o contexto macro favorece ou dificulta a operação.

3. 🔍 ATIVOS QUASE LÁ: Mencione ativos que quase passaram no filtro e o que falta para completar o setup.

4. ⚠️ RISCOS DO MOMENTO: 2-3 fatores que podem invalidar os setups.

5. 💡 VEREDICTO: Uma frase sobre o momento de mercado para swing trade.

Seja direto e objetivo. Máximo 1800 caracteres.
Sempre termine com: "⚠️ Análise educacional. Não é recomendação de investimento."
"""

    # Endpoint da API REST do Gemini (sem SDK, só requests)
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models"
        f"/gemini-1.5-flash:generateContent?key={GEMINI_APIKEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 1024,
            "temperature":     0.4,   # mais focado e menos criativo para análise técnica
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"  Erro Gemini: {e}")
        try:
            print(f"  Resposta: {resp.text[:300]}")
        except Exception:
            pass
        return f"⚠️ Erro na análise de IA: {e}"


# ════════════════════════════════════════════════════════════════
#  🚀  EXECUÇÃO PRINCIPAL
# ════════════════════════════════════════════════════════════════

def rodar_analise():
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"\n{'═'*65}")
    print(f"  🤖 ROBÔ TRADER PRO — {agora}")
    print(f"{'═'*65}\n")

    todos_dados    = []
    setups_validos = []

    for categoria, ativos in ATIVOS.items():
        print(f"\n📂 {categoria}")
        for ativo in ativos:
            resultado = analisar_ativo_completo(ativo["ticker"], ativo["nome"])
            if resultado:
                resultado["categoria"] = categoria
                todos_dados.append(resultado)
                if resultado["setup_valido"]:
                    setups_validos.append(resultado)

    if not todos_dados:
        print("Nenhum dado coletado. Abortando.")
        return

    # ── MSG 1: Painel geral ─────────────────────────────────────
    linhas = [f"📊 *Robô Trader PRO — {agora}*\n"]
    for cat in ATIVOS.keys():
        ativos_cat = [d for d in todos_dados if d["categoria"] == cat]
        if not ativos_cat:
            continue
        linhas.append(f"*{cat}*")
        for d in ativos_cat:
            em_tend = {"ALTA": "📈", "BAIXA": "📉", "INDEFINIDA": "➡️"}.get(d["tendencia"], "➡️")
            pb_icon = "🔄" if d["e_pullback"] else "  "
            setup_icon = "✅" if d["setup_valido"] else f"[{d['criterios_count']}/6]"
            linhas.append(
                f"  {setup_icon} {pb_icon} {d['nome']}: {d['preco']} "
                f"({'+' if d['var_1d']>=0 else ''}{d['var_1d']}%) "
                f"| {em_tend} {d['tendencia']} | RSI {d['rsi_diario']}"
            )
        linhas.append("")

    linhas.append("✅=Setup válido  🔄=Pullback  [n/6]=critérios")
    enviar_whatsapp("\n".join(linhas))

    # ── MSG 2: Detalhes dos setups válidos ──────────────────────
    if setups_validos:
        alerta = [f"⚡ *{len(setups_validos)} SETUP(S) VÁLIDO(S) — {agora}*\n"]
        for d in setups_validos:
            direcao_emoji = "🟢 COMPRA" if d["direcao"] == "COMPRA" else "🔴 VENDA"
            alerta.append(
                f"{direcao_emoji} — *{d['nome']}* ({d['ticker']})\n"
                f"  💰 Entrada:    {d['preco']}\n"
                f"  🛑 Stop:       {d['stop']} ({d['risco_pct']}% risco | {d['stop_metodo']})\n"
                f"  🎯 Alvo:       {d['alvo']} ({d['potencial_pct']}% potencial)\n"
                f"  📐 R:R:        {d['rr']}:1  ({'✅ Aprovado' if d['rr_valido'] else '❌ Reprovado'})\n"
                f"  📊 Expectativa: {d['expectativa_pct']}%  ({'✅ Positiva' if d['expectativa_pos'] else '❌ Negativa'})\n"
                f"  📉 RSI diário: {d['rsi_diario']}\n"
                f"  📦 Volume:     {d['vol_relativo']}x média\n"
                f"  🗓️ Tendência:  {d['tendencia']} (score {d['tendencia_score']}/4)\n"
            )
        enviar_whatsapp("\n".join(alerta))
    else:
        enviar_whatsapp(
            f"🔍 *Nenhum setup válido agora — {agora}*\n\n"
            f"Nenhum ativo passou em todos os {6} critérios simultaneamente.\n"
            f"Continue monitorando — o mercado muda!"
        )

    # ── MSG 3: Análise da IA ────────────────────────────────────
    print("\n🧠 Enviando dados para o Gemini...")
    analise = analisar_com_gemini(todos_dados, setups_validos)
    print("\n" + analise)
    enviar_whatsapp(f"🧠 *ANÁLISE DA IA (Gemini)*\n\n{analise}")

    print(f"\n✅ Concluído em {datetime.now().strftime('%H:%M:%S')}")
    print(f"   {len(setups_validos)} setup(s) válido(s) de {len(todos_dados)} ativos analisados.")


if __name__ == "__main__":
    rodar_analise()
