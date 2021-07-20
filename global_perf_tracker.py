import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import warnings
warnings.filterwarnings("ignore")
from datetime import date, timedelta
import streamlit as st
from io import BytesIO
import base64
import plotly.express as px
import plotly.graph_objects as go
import plotly


import ipywidgets as widgets
from ipywidgets import interact, interact_manual
from IPython.core.display import display, HTML


#Import Master Data
rets_cols = ['1D', '1W', '1M', '3M', 'YTD']

@st.cache(suppress_st_warning=True)
def load_eq_data():
    data = pd.read_excel('GSTOCKS_N.xlsx',engine='openpyxl')
    data.columns = ["Ticker","Name","Market Cap","Country","Industry","Sub-Industry","1D","1M","3M","YTD","ROE","ROCE","EBITDA (%)",
    "Profit (%)","P/E","Rev YoY","EBITDA YoY","Profit YoY","Rev T12M","FCF T12M", "1W"]
    data[rets_cols] = data[rets_cols]/100
    data['Market Cap'] = data['Market Cap']/10**9
    data = data[['Ticker', 'Name', 'Country', 'Industry', 'Sub-Industry', 'Market Cap',
    '1D', '1W', '1M', '3M', 'YTD']]
    data['Country'].replace("United Arab Emirates", "UAE", inplace=True)
    data['Country'].replace("Trinidad & Tobago", "Trinidad", inplace=True)
    return data

data = load_eq_data()

all_countries = ["All"] + list(data['Country'].unique())



#DEFINE FUNCTIONS:


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data

def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    val = to_excel(df)
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Export to Excel</a>' # decode b'abc' => abc


#CALCULATE MCAP WEIGHTED RETURNS
def mcap_weighted(df, rets_cols, groupby, style=True, reit=False):
    old_mcap = (1/(1+df[rets_cols])).multiply(df['Market Cap'], axis='rows')
    old = old_mcap.join(df['Market Cap'])
    old.iloc[:,:-1] = -old.iloc[:,:-1].subtract(old.iloc[:,-1], axis='rows')
    change_sum = old.join(df[groupby]).groupby(groupby).sum().iloc[:,:-1]
    old_sum = old_mcap.join(df[groupby]).groupby(groupby).sum()
    mcap_weight = pd.DataFrame(df.groupby(groupby).sum()['Market Cap']).merge(change_sum.divide(old_sum, axis='rows'), on=groupby)
    df = mcap_weight
    df[rets_cols] = df[rets_cols]*100
    if reit == True:
        subs = ["1D","1W","1M","3M","6M","YTD"]
    else:
        subs = ["1D","1W","1M","3M","YTD"]
    if style==True:
        df = df.sort_values(by='YTD', ascending=False).style.format('{0:,.2f}%', subset=subs)\
                       .format('{0:,.2f}B', subset=["Market Cap"])\
                       .background_gradient(cmap='RdYlGn', subset=subs)
    else:
        df = df.sort_values(by='YTD', ascending=False)
    return df


#INTERACTIVE PIVOT TABLE
def pivot_table(region, country, ind, maxmcap, minmcap, category):
    df = data.copy()
    df = df[(df["Market Cap"]<=maxmcap) & (df["Market Cap"]>minmcap)]
    rets_cols = ['1D', '1W', '1M', '3M', 'YTD']
    if country != "All" and ind==["All"]:
        df = df[df['Country'].isin(country)]
        df = mcap_weighted(df, rets_cols, category)
    elif country != "All" and ind==["None"]:
        if region!='All Markets':
            df = df[df['Country'].isin(region)]
            df = mcap_weighted(df, rets_cols, 'Country')
        else:
            df = df[df['Country'].isin(country)]
            df = mcap_weighted(df, rets_cols, 'Country')
    elif country == "All" and ind==["All"]:
        if region!='All Markets':
            df = df[df['Country'].isin(region)]
            df = mcap_weighted(df, rets_cols, category)
        else:
            df = mcap_weighted(df, rets_cols, category)
    elif country == "All" and ind==["None"]:
        if region!='All Markets':
            df = df[df['Country'].isin(region)]
            df = mcap_weighted(df, rets_cols, 'Country')
        else:
            df = mcap_weighted(df, rets_cols, 'Country')                        
    elif country == "All" and ind!=["All"]:
        df = df[(df['Country'].isin(region)) & (df[category].isin(ind))]
        df = mcap_weighted(df, rets_cols, 'Country')        
    else:
        df = df[(df['Country'].isin(country)) & (df[category].isin(ind))]
        df = df.set_index('Ticker')
        df = df.fillna(0).sort_values(by='YTD', ascending=False).style.format('{0:,.2%}', subset=rets_cols)\
                    .format('{0:,.1f}B', subset=['Market Cap'])\
                    .background_gradient(cmap='RdYlGn', subset=rets_cols)
    return df



#DEFINE REGION LISTS
full = list(data['Country'].unique())

allclean = data.groupby('Country').sum()
allclean = allclean[allclean['Market Cap']>=50].index.to_list()

em = ['Argentina', 'Brazil', 'Chile', 'China', 'Colombia', 'Czech Republic', 'Egypt', 'Greece', 'Hungary', 'India', 'Indonesia',
  'South Korea', 'Kuwait', 'Malaysia', 'Mexico', 'Peru', 'Philippines', 'Poland', 'Qatar', 'Russia', 'South Africa',
  'Taiwan', 'Thailand', 'Turkey', 'United Arab Emirates', 'Vietnam', 'Saudi Arabia', 'Pakistan']

dm = list(set(full).difference(em))

dmexus = list(set(full).difference(em).difference(['United States']))

asia_pacific = ['China', 'India', 'Indonesia', 'South Korea', 'Malaysia', 'Pakistan', 'Philippines',
           'Taiwan', 'Thailand', 'Hong Kong', 'Japan', 'New Zealand', 'Australia', 'Singapore']

emexchina = ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Czech Republic', 'Egypt', 'Greece', 'Hungary', 'India', 'Indonesia',
  'South Korea', 'Kuwait', 'Malaysia', 'Mexico', 'Peru', 'Philippines', 'Poland', 'Qatar', 'Russia', 'South Africa',
  'Taiwan', 'Thailand', 'Turkey', 'United Arab Emirates', 'Vietnam', 'Saudi Arabia', 'Pakistan']

emasia = ['China', 'India', 'Indonesia', 'South Korea', 'Malaysia', 'Pakistan', 'Philippines', 'Taiwan', 'Thailand']

europe = ['Austria', 'Belgium', 'Denmark', 'Finland', 'France', 'Germany', 'Italy', 'Netherlands', 'Norway',
          'Spain', 'Sweden', 'Switzerland', 'United Kingdom', 'Portugal']

latam = ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Mexico', 'Peru']

emea = ['Czech Republic', 'Egypt', 'Greece', 'Hungary', 'Kuwait', 'Poland', 'Qatar', 'Russia', 'Saudi Arabia',
        'South Africa', 'Turkey', 'United Arab Emirates']

me=['Bahrain', 'Cyprus', 'Egypt', 'Iran', 'Iraq','Israel','Jordan','Kuwait','Lebanon','Oman','Qatar','Saudi Arabia','Turkey','UAE']

india = ['India']


#INTERACTIVE TABLE
st.markdown('# Global Equity Performance Pivot Table')

with st.beta_expander('Show Filters'):
    d1, d2, d3= st.beta_columns(3)
    region = d1.selectbox('Region: ', ['All-Min $50B MCap', 'All Markets', 'Developed Markets', 'DM ex-US', 'Europe', 'Emerging Markets', 'EM ex-China', 'EM - Asia',
                                      'EMEA','Latin America','Middle East', 'Asia Pacific', 'India'])
  
    minmcap = d2.number_input('Minimum MCap (Bn USD): ', min_value=data['Market Cap'].min(), max_value=data['Market Cap'].max(), value=data['Market Cap'].min(), step=0.1, key ='eqpivot-min')
    maxmcap = d3.number_input('Maximum MCap (Bn USD): ', min_value=data['Market Cap'].min(), max_value=data['Market Cap'].max(), value=data['Market Cap'].max(), step=0.1, key='eqpivot-max')

    if region == 'All Markets':
        regional_code = full.copy()
    elif region == 'Developed Markets':
        regional_code = dm.copy()
    elif region == 'Emerging Markets':
        regional_code = em.copy()
    elif region == 'EM - Asia':
        regional_code = emasia.copy()
    elif region == 'Europe':
        regional_code = europe.copy()
    elif region == 'Latin America':
        regional_code = latam.copy()
    elif region == 'Asia Pacific':
        regional_code = asia_pacific.copy()
    elif region == 'EM ex-China':
        regional_code = emexchina.copy()
    elif region == 'DM ex-US':
        regional_code = dmexus.copy()    
    elif region == 'India':
        regional_code = india.copy()
    elif region == 'EMEA':
        regional_code = emea.copy()
    elif region == 'Middle East':
        regional_code = me.copy()
    elif region == 'All-Min $50B MCap':
        regional_code = allclean.copy()    

    c1, c2, c3 = st.beta_columns(3)

    country_code = c1.selectbox('Country: ', ['All'] + regional_code)
    category = c2.selectbox('GICS Level: ', ['Industry', 'Sub-Industry'])
    inds_code = c3.multiselect(str(category)+': ',  ['All', 'None']+ list(data[category].unique()), default=['All'])

if country_code!='All':
    st.write(pivot_table(regional_code, [country_code], inds_code, maxmcap, minmcap, category))
    st.markdown(get_table_download_link(pivot_table(regional_code, [country_code], inds_code, maxmcap, minmcap, category)), unsafe_allow_html=True)
else:
    st.write(pivot_table(regional_code, country_code, inds_code, maxmcap, minmcap, category))
    st.markdown(get_table_download_link(pivot_table(regional_code, country_code, inds_code, maxmcap, minmcap, category)), unsafe_allow_html=True)



st.markdown('# Regional Industry Returns')
def regional_sect_perf(period='YTD', level = 'Sub-Industry'):
    """
    """
    
    region_names = ['All', 'DM', 'DM ex-US', 'Europe', 'EM', 'EM ex-China', 'EM-Asia','EMEA','LatAm','Middle East', 'APAC']
    region_dfs = [full, dm, dmexus, europe, em, emexchina, emasia, emea, latam, me, asia_pacific]
    matrix = pd.DataFrame(index=data[level].unique())
    matrix.index.name = level
    for i in range(11):
        new_df = data[data['Country'].isin(region_dfs[i])]
        new_df = new_df[(new_df["Market Cap"]<=maxmcap) & (new_df["Market Cap"]>minmcap)]    
        reg  = pd.DataFrame(mcap_weighted(new_df, rets_cols, level, style=False)[period])
        reg.columns = [region_names[i]]
        matrix = matrix.join(reg, on=level)

    matrix = matrix.sort_values(by='All', ascending = False).drop(np.nan, axis=0).fillna(0).style.format('{0:,.2f}%')\
                    .background_gradient(cmap='RdYlGn')
    return matrix

e1, e2 = st.beta_columns(2)
regional_period = e1.selectbox('Period: ', ['YTD', '1D', '1W','1M', '3M'])
classification_level = e2.selectbox('GICS Level: ', ['Sub-Industry', 'Industry'])
f1, f2= st.beta_columns(2)
minmcap = f1.number_input('Minimum MCap (Bn USD): ', min_value=data['Market Cap'].min(), max_value=data['Market Cap'].max(), value=data['Market Cap'].min(), step=0.1, key ='eqregion-min')
maxmcap = f2.number_input('Maximum MCap (Bn USD): ', min_value=data['Market Cap'].min(), max_value=data['Market Cap'].max(), value=data['Market Cap'].max(), step=0.1, key='eqregion-max')
st.write(regional_sect_perf(period = regional_period, level = classification_level))
st.markdown(get_table_download_link(regional_sect_perf(period = regional_period, level = classification_level)), unsafe_allow_html=True)