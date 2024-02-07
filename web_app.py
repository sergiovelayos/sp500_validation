#import required libraries
import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd
import pandas_datareader as pdr
import matplotlib.pyplot as plt
import io

st.set_page_config(
   page_title="Rentabilidad bolsa",
   page_icon="🧊",
#    layout="wide",
#    initial_sidebar_state="expanded",
)
#function calling local css sheet
def local_css(file_name):
    with open(file_name) as f:
        st.sidebar.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

#local css sheet
local_css("style.css")


# Load SP500 table from Wikipedia
sp500url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
sp500 = pd.read_html(sp500url)[0]

# Create dictionary to map Company("Empresa") and Symbol
mapa_empresas_a_simbolos = dict(zip(sp500['Security'], sp500['Symbol']))

#main function
def main():

    st.title('Lista SP500')
    st.write(f'''
             [Fuente]({sp500url}) ''')
    st.write(sp500)
    
    # Download SP500
    @st.cache
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

    csv = convert_df(sp500)

    st.download_button(
        label="Descargar ListaSP500 (csv)",
        data=csv,
        file_name='large_df.csv',
        mime='text/csv  ',
    )

    # User picks a company name but we return the company symbol value
    nom_emp = st.selectbox('Elige una empresa',sp500['Security'])
    selected_stock =  mapa_empresas_a_simbolos[nom_emp]

    #get data on searched ticker
    stock_data = yf.Ticker(selected_stock)
    
    #get historical data for searched ticker
    fecha_inicio = st.date_input("Elige fecha de inicio:")
    fecha_fin = st.date_input("y fecha fin:")
    stock_df = stock_data.history(period='1d', start=fecha_inicio, end=fecha_fin)

    # Convert DatetimeIndex to Date
    stock_df.index = pd.to_datetime(stock_df.index, utc=True)  
    stock_df.index = stock_df.index.date 

    st.subheader("""Evolución del precio de cierre para """ + nom_emp)
    #print line chart with daily closing prices for searched ticker
    st.line_chart(stock_df.Close)
    
    stock_line_chart = stock_df.rename(columns={'Volume':'Volumen','Close':'Precio cierre'})
    st.line_chart(stock_line_chart, x= 'Precio cierre', y = 'Volumen')
    
    st.write("Tabla Stock con dividendos")    
    # Add column that accumulates dividends
    stock_df['Dividendos acumulados'] = stock_df.Dividends.cumsum()

    # Add column with % return between starting and ending date
    stock_df['Rentabilidad acumulada'] = (stock_df['Close'] / stock_df['Close'].iloc[0] - 1) * 100
    st.write(stock_df)

    # Ahora, tu DataFrame 'stock_df' tendrá el índice en formato date
    st.write(stock_df)
    
    # # Show df.info in Streamlit
    # buffer = io.StringIO()
    # stock_df.info(buf=buffer, verbose=True)
    # s = buffer.getvalue()
    # st.text(s)

    # Resample para obtener rentabilidad y dividendos acumulados mensuales
    st.title("Rentabilidades totales")
    st.write("Rentabilidad entre la fecha inicio y fin de la compañía seleccionada")
    
    stock_df.index = pd.to_datetime(stock_df.index, utc=True)
    stock_df_resampled = stock_df.resample('M').agg({
        'Close': 'last',
        'Rentabilidad acumulada': lambda x: x.iloc[-1] - x.iloc[0],
        'Dividends': 'sum'
    }).ffill()

    # Calcular rentabilidad total a nivel mensual
    stock_df_resampled['Rentabilidad total'] = (stock_df_resampled['Close'] / stock_df_resampled['Close'].iloc[0] - 1) * 100
    
        # Convert DatetimeIndex to Date
    stock_df_resampled.index = pd.to_datetime(stock_df_resampled.index, utc=True)  
    stock_df_resampled.index = stock_df_resampled.index.date 

    st.write(stock_df_resampled)
    # st.write(stock_df_resampled.index.min())
    fecha_rent_max = stock_df_resampled.index.max()
    st.write(stock_df_resampled.loc[fecha_rent_max])
    
    # Usar st.number_input para introducir un número entero
    cantidad_ahorro = st.number_input("Introduce la cantidad de ahorro mensual", min_value=0, step=100)

    rango_fechas = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='MS')

    datos = {'Fecha': rango_fechas, 'Ahorro': cantidad_ahorro}

    # Paso 4: Convertir el diccionario en un DataFrame
    ahorros = pd.DataFrame(datos)

    ahorros['Ahorros acumulados'] = ahorros.Ahorro.cumsum()

    ahorros_max_acumulados = ahorros['Ahorros acumulados'].max()

    # Mostrar la cantidad introducida acumulada
    st.metric(label=f"Cantidad de ahorro acumulado entre {fecha_inicio} y {fecha_fin}",
              value=ahorros_max_acumulados)

    # Seleccionar un subconjunto de empresas
    multi_empresas_selector = st.multiselect("Selecciona las empresas", sp500['Security'].tolist())

    # Convertir la lista en una tupla
    multi_empresas_tupla = tuple(multi_empresas_selector)

    # Mostrar el DataFrame resultante
    st.write("Empresas seleccionadas:")
    # st.write(df_filtrado)

    multi_selected_stock =  [mapa_empresas_a_simbolos[empresa] for empresa in multi_empresas_tupla]

    #get data on searched ticker
    multi_stock_data = [yf.Ticker(stock) for stock in multi_selected_stock]
    
    #get historical data for searched ticker
    multi_stock_df = [stock_data.history(period='1d', start=fecha_inicio, end=fecha_fin) for stock_data in multi_stock_data]

    # Crear un DataFrame consolidado para mostrar en la tabla
    tabla_consolidada = pd.DataFrame()
    for i, empresa in enumerate(multi_empresas_selector):
        cambios = (multi_stock_df[i]['Close'] / multi_stock_df[i]['Close'].iloc[0] - 1) * 100
        cambios.dropna(inplace=True)
        tabla_consolidada[empresa] = cambios

    # Mostrar la tabla con el cambio del precio de cierre
    st.write("Cambios en el precio de cierre entre", fecha_inicio, "y", fecha_fin)

    # Convert DatetimeIndex to Date
    tabla_consolidada.index = pd.to_datetime(tabla_consolidada.index, utc=True)  
    tabla_consolidada.index = tabla_consolidada.index.date 

    st.write(tabla_consolidada)
    st.title("Rentabilidades acumuladas")
    st.line_chart(tabla_consolidada)

    st.write(tabla_consolidada)

    # Crear un DataFrame consolidado para mostrar en la tabla
    tabla_consolidada = pd.DataFrame()
    for i, empresa in enumerate(multi_empresas_selector):
        cambios = (multi_stock_df[i]['Close'] / multi_stock_df[i]['Close'].iloc[0] - 1) * 100
        cambios.dropna(inplace=True)
        tabla_consolidada[f'{empresa}_cambios'] = cambios
        
        valor_max = multi_stock_df[i]['High']
        valor_max.dropna(inplace=True)
        tabla_consolidada[f'{empresa}_valor_max'] = valor_max

        # Nueva columna que divide el ahorro mensual entre el precio de cierre
        tabla_consolidada[f'{empresa}_ahorro_dividido'] = (cantidad_ahorro / multi_stock_df[i]['Close']).cumsum()


    st.write(tabla_consolidada)
    st.write(ahorros)
    
    # ###########################
    # # Line chart con 2 líneas #
    # ###########################
    # st.title("Line chart con 2 ejes")
    # # Add one more company to compare
    # st.line_chart(stock_df[['Close', 'Low']], use_container_width=True)


    # # Fred data
    # st.write("Real gross domestic product per capita (US)")
    # # Change first parameter to change chart
    # df = pdr.DataReader('A939RX0Q048SBEA', 'fred',fecha_inicio,fecha_fin)
    # st.line_chart(df)


    # st.subheader("""Dividends for """ + selected_stock)
    # div_sum = stock_df.Dividends
    # st.metric(label="Dividendos", value="3,456$", delta="5$")


    # st.subheader("""Last **closing price** for """ + selected_stock)
    # #define variable today 
    # today = datetime.today().strftime('%Y-%m-%d')
    # #get current date data for searched ticker
    # stock_lastprice = stock_data.history(period='1d', start=today, end=today)
    # #get current date closing price for searched ticker
    # last_price = (stock_lastprice.Close)
    # #if market is closed on current date print that there is no data available
    # if last_price.empty == True:
    #     st.write("No data available at the moment")
    # else:
    #     st.write(last_price)
    
    # #get daily volume for searched ticker
    # st.subheader("""Daily **volume** for """ + selected_stock)
    # st.line_chart(stock_df.Volume)

    # #additional information feature in sidebar
    # st.sidebar.subheader("""Mostrar más indicadores para el empresa seleccionada""")
    # #checkbox to display stock actions for the searched ticker
    # actions = st.sidebar.checkbox("Stock Actions")
    # if actions:
    #     st.subheader("""Stock **actions** for """ + selected_stock)
    #     display_action = (stock_data.actions)
    #     if display_action.empty == True:
    #         st.write("No data available at the moment")
    #     else:
    #         st.write(display_action)
    
    # #checkbox to display quarterly financials for the searched ticker
    # financials = st.sidebar.checkbox("Quarterly Financials")
    # if financials:
    #     st.subheader("""**Quarterly financials** for """ + selected_stock)
    #     display_financials = (stock_data.quarterly_financials)
    #     if display_financials.empty == True:
    #         st.write("No data available at the moment")
    #     else:
    #         st.write(display_financials)

    # #checkbox to display list of institutional shareholders for searched ticker
    # major_shareholders = st.sidebar.checkbox("Institutional Shareholders")
    # if major_shareholders:
    #     st.subheader("""**Institutional investors** for """ + selected_stock)
    #     display_shareholders = (stock_data.institutional_holders)
    #     if display_shareholders.empty == True:
    #         st.write("No data available at the moment")
    #     else:
    #         st.write(display_shareholders)

    # #checkbox to display quarterly balance sheet for searched ticker
    # balance_sheet = st.sidebar.checkbox("Quarterly Balance Sheet")
    # if balance_sheet:
    #     st.subheader("""**Quarterly balance sheet** for """ + selected_stock)
    #     display_balancesheet = (stock_data.quarterly_balance_sheet)
    #     if display_balancesheet.empty == True:
    #         st.write("No data available at the moment")
    #     else:
    #         st.write(display_balancesheet)

    # #checkbox to display quarterly cashflow for searched ticker
    # cashflow = st.sidebar.checkbox("Quarterly Cashflow")
    # if cashflow:
    #     st.subheader("""**Quarterly cashflow** for """ + selected_stock)
    #     display_cashflow = (stock_data.quarterly_cashflow)
    #     if display_cashflow.empty == True:
    #         st.write("No data available at the moment")
    #     else:
    #         st.write(display_cashflow)

    # #checkbox to display quarterly earnings for searched ticker
    # earnings = st.sidebar.checkbox("Quarterly Earnings")
    # if earnings:
    #     st.subheader("""**Quarterly earnings** for """ + selected_stock)
    #     display_earnings = (stock_data.quarterly_earnings)
    #     if display_earnings.empty == True:
    #         st.write("No data available at the moment")
    #     else:
    #         st.write(display_earnings)

    # #checkbox to display list of analysts recommendation for searched ticker
    # analyst_recommendation = st.sidebar.checkbox("Analysts Recommendation")
    # if analyst_recommendation:
    #     st.subheader("""**Analysts recommendation** for """ + selected_stock)
    #     display_analyst_rec = (stock_data.recommendations)
    #     if display_analyst_rec.empty == True:
    #         st.write("No data available at the moment")
    #     else:
    #         st.write(display_analyst_rec)

if __name__ == "__main__":
    main()
