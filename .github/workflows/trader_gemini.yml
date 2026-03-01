name: Robô Trader PRO — Gemini (Gratuito)

on:
  schedule:
    # Segunda a sexta, a cada 30 min, das 10h às 17h (Brasília = UTC-3)
    - cron: "0,30 13-20 * * 1-5"
    # Análise de abertura (10h Brasília)
    - cron: "0 13 * * 1-5"
    # Análise de fechamento (17h Brasília)
    - cron: "0 20 * * 1-5"
  workflow_dispatch:  # Permite rodar manualmente

jobs:
  analisar:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Baixar código
        uses: actions/checkout@v4

      - name: Configurar Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Instalar dependências
        run: pip install yfinance pandas numpy requests

      - name: Rodar análise e enviar WhatsApp
        env:
          CALLMEBOT_PHONE:  ${{ secrets.CALLMEBOT_PHONE }}
          CALLMEBOT_APIKEY: ${{ secrets.CALLMEBOT_APIKEY }}
          GEMINI_API_KEY:   ${{ secrets.GEMINI_API_KEY }}
        run: python robo_trader_gemini.py
