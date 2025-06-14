import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Symbol & FX Viewer", layout="wide")
ALPHA_KEY = "LIM4EY3MC0CJK5T0"

page = st.sidebar.selectbox(
    "Seleziona pagina",
    ["Symbol × EUR", "Symbol High/Low", "USD → EUR FX"]
)

#############################
if page == "Symbol × EUR":
    st.title("💶 Symbol Price: USD & EUR Overlay")

    symbol = st.text_input("Simbolo (es. DIA, AAPL)", value="DIA")
    start = st.date_input("Data inizio", value=pd.to_datetime("2025-01-01"))
    end = st.date_input("Data fine", value=pd.to_datetime(datetime.today().strftime("%Y-%m-%d")))

    if st.button("Load Combined Chart"):
        # 🏷️ Fetch symbol prices
        resp_s = requests.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "compact",
                "apikey": ALPHA_KEY
            }
        )
        data_s = resp_s.json().get("Time Series (Daily)", {})
        if not data_s:
            st.error("Nessun dato simbolo – verifica")
            st.stop()

        df_s = pd.DataFrame(data_s).T.astype(float)
        df_s.index = pd.to_datetime(df_s.index)
        df_s.sort_index(inplace=True)
        df_s = df_s.loc[start:end]
        df_s["close"] = df_s["4. close"]

        # 💱 Fetch USD→EUR rates
        resp_fx = requests.get(
            f"https://api.frankfurter.app/{start}..{end}?from=USD&to=EUR"
        )
        rates = resp_fx.json().get("rates", {})
        if not rates:
            st.error("Errore cambio USD→EUR")
            st.stop()

        df_fx = pd.DataFrame(rates).T
        df_fx.index = pd.to_datetime(df_fx.index)
        df_fx.columns = ["usd_eur"]

        # 🔗 Join and convert
        df = df_s[["close"]].join(df_fx, how="inner")
        df["close_eur"] = df["close"] * df["usd_eur"]

        # --- EUR calculations ---
        eur = df["close_eur"]
        eur_first = eur.iloc[0]
        eur_last = eur.iloc[-1]
        eur_min = eur.min()
        eur_max = eur.max()
        eur_min_idx = eur.idxmin()
        eur_max_idx = eur.idxmax()

        # % dal primo all'ultimo
        eur_pct_first_last = (eur_last - eur_first) / eur_first * 100
        # % dal max al min
        eur_pct_max_min = (eur_min - eur_max) / eur_max * 100
        # % dal min a oggi
        eur_pct_min_today = (eur_last - eur_min) / eur_min * 100

        # --- USD calculations ---
        usd = df["close"]
        usd_first = usd.iloc[0]
        usd_last = usd.iloc[-1]
        usd_min = usd.min()
        usd_max = usd.max()
        usd_min_idx = usd.idxmin()
        usd_max_idx = usd.idxmax()

        usd_pct_first_last = (usd_last - usd_first) / usd_first * 100
        usd_pct_max_min = (usd_min - usd_max) / usd_max * 100
        usd_pct_min_today = (usd_last - usd_min) / usd_min * 100

        # --- USD/EUR percentuale ---
        usd_eur_first = df["usd_eur"].iloc[0]
        usd_eur_last = df["usd_eur"].iloc[-1]
        usd_eur_pct = (usd_eur_last - usd_eur_first) / usd_eur_first * 100

        # --- Plot ---
        import plotly.graph_objects as go
        fig = px.line(
            df,
            x=df.index,
            y=["close_eur", "close"],
            labels={"value": f"{symbol} price", "index": "Date", "variable": "Currency"},
            title=f"{symbol} Price: USD (rosso) & EUR (blu)\n{start} → {end}"
        )
        fig.update_traces(selector=dict(name="close_eur"), line_color="blue", name="EUR")
        fig.update_traces(selector=dict(name="close"), line_color="red", name="USD")
        fig.update_traces(mode="lines+markers", hovertemplate="%{x}<br>%{variable}: %{y:.2f}")

        # Linea dal primo all'ultimo punto per EUR
        fig.add_trace(go.Scatter(
            x=[df.index[0], df.index[-1]],
            y=[eur_first, eur_last],
            mode="lines",
            line=dict(color="blue", dash="dash"),
            name="EUR trend (inizio→oggi)"
        ))
        # Linea dal primo all'ultimo punto per USD
        fig.add_trace(go.Scatter(
            x=[df.index[0], df.index[-1]],
            y=[usd_first, usd_last],
            mode="lines",
            line=dict(color="red", dash="dash"),
            name="USD trend (inizio→oggi)"
        ))
        # Linea EUR max→min
        fig.add_trace(go.Scatter(
            x=[eur_max_idx, eur_min_idx],
            y=[eur_max, eur_min],
            mode="lines",
            line=dict(color="blue", dash="dot"),
            name="EUR max→min"
        ))
        # Linea EUR min→oggi
        fig.add_trace(go.Scatter(
            x=[eur_min_idx, df.index[-1]],
            y=[eur_min, eur_last],
            mode="lines",
            line=dict(color="blue", dash="dot"),
            name="EUR min→oggi"
        ))
        # Linea USD max→min
        fig.add_trace(go.Scatter(
            x=[usd_max_idx, usd_min_idx],
            y=[usd_max, usd_min],
            mode="lines",
            line=dict(color="red", dash="dot"),
            name="USD max→min"
        ))
        # Linea USD min→oggi
        fig.add_trace(go.Scatter(
            x=[usd_min_idx, df.index[-1]],
            y=[usd_min, usd_last],
            mode="lines",
            line=dict(color="red", dash="dot"),
            name="USD min→oggi"
        ))

        st.plotly_chart(fig, use_container_width=True)

        # Mostra tutte le percentuali in due colonne, con USD/EUR in mezzo
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.markdown(
                f"""
                ### USD
                - **% inizio→oggi:** {usd_pct_first_last:+.2f}%
                - **% max→min:** {usd_pct_max_min:+.2f}%
                - **% min→oggi:** {usd_pct_min_today:+.2f}%
                """
            )
        with col2:
            st.markdown(
                f"""
                ### USD/EUR
                - **% inizio→oggi:** {usd_eur_pct:+.2f}%
                """
            )
        with col3:
            st.markdown(
                f"""
                ### EUR
                - **% inizio→oggi:** {eur_pct_first_last:+.2f}%
                - **% max→min:** {eur_pct_max_min:+.2f}%
                - **% min→oggi:** {eur_pct_min_today:+.2f}%
                """
            )

        # 📦 Show raw JSON
        st.subheader("📦 JSON raw")
        st.write("— Symbol JSON —")
        st.json(data_s)
        st.write("— FX JSON —")
        st.json(resp_fx.json())

#############################
elif page == "Symbol High/Low":
    st.title("🔍 Symbol High & Low via Alpha Vantage")
    symbol = st.text_input("Inserisci simbolo (es. DIA, AAPL)", value="DIA")
    if st.button("Load JSON & Chart"):
        resp = requests.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "compact",
                "apikey": ALPHA_KEY
            }
        )
        data = resp.json()
        ts = data.get("Time Series (Daily)", {})
        if not ts:
            st.error("Nessun dato disponibile. Verifica il simbolo o i limiti API.")
            st.stop()

        df = pd.DataFrame(ts).T.astype(float)
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        df = df.rename(columns={"2. high": "high", "3. low": "low"})

        fig = px.line(
            df,
            x=df.index,
            y=["high", "low"],
            labels={"value": "Prezzo", "index": "Data", "variable": "Serie"},
            title=f"{symbol} – High (blu) & Low (rosso)"
        )
        fig.update_traces(selector=dict(name="high"), line_color="blue")
        fig.update_traces(selector=dict(name="low"), line_color="red")
        fig.update_traces(mode="lines+markers", hovertemplate="%{x}<br>%{variable}: %{y:.2f}")
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("📦 JSON grezzo")
        st.json(data)

#############################
elif page == "USD → EUR FX":
    st.title("💱 USD → EUR Exchange Rate via Frankfurter")
    start = st.date_input("Data inizio", value=pd.to_datetime("2025-01-01"))
    end = st.date_input("Data fine", value=pd.to_datetime("2025-06-12"))
    if st.button("Load FX JSON & Chart"):
        resp_fx = requests.get(f"https://api.frankfurter.app/{start}..{end}?from=USD&to=EUR")
        data_fx = resp_fx.json()
        if resp_fx.status_code != 200 or "rates" not in data_fx:
            st.error("Errore nel recupero dati cambio USD→EUR")
            st.stop()

        df_fx = pd.DataFrame(data_fx["rates"]).T
        df_fx.index = pd.to_datetime(df_fx.index)
        df_fx.columns = ["usd_eur"]

        fig_fx = px.line(
            df_fx,
            x=df_fx.index,
            y="usd_eur",
            labels={"usd_eur": "EUR per 1 USD", "index": "Date"},
            title="Tasso USD → EUR Storico"
        )
        fig_fx.update_traces(mode="lines+markers", hovertemplate="%{x}<br>EUR per USD: %{y:.4f}")
        st.plotly_chart(fig_fx, use_container_width=True)
        st.subheader("📦 JSON cambio grezzo")
        st.json(data_fx)