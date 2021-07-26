#%%
from enum import unique
from numpy.core.defchararray import title
import streamlit as st  
import pandas as pd
import numpy as np

import time
import altair as alt
import pydeck as pdk

from geoLookup import geoLookup as geo

#%%
st.title("API Pricing Explorer: Explore the drug prices for API all over the world:")


st.subheader("Nguyen Dao Vu")
#%%
# load and manipulate data
@st.cache
def loadData(name):
    data_table = pd.read_csv(name)
    return data_table

data = loadData("PharmaCompass_600_clean.csv")

unique_apis = sorted(list(set(list(data["API"].values))))

#%%

chosenAPI = st.sidebar.selectbox("Select API of Interests", unique_apis)
st.header("API = " +chosenAPI)

@st.cache
def getAPIdf(chosenAPI_in, data_in):
    dt = data_in[data_in["API"]==chosenAPI_in]
    dt = dt.loc[(dt["quantity_in_KG"]>= 1)&(dt["productDescription"]=="API"), :]
    dt.drop(dt.columns[[0,1]], axis=1, inplace =True)
    dt['customerCountry'] = dt['customerCountry'].str.upper()
    dt['supplierCountry'] = dt['supplierCountry'].str.upper()
    return dt

def getSummary(dataTable, by = "year"):
    greater_than_1kg = dataTable["quantity_in_KG"].values >= 1

    dt = dataTable.loc[greater_than_1kg, :]
    dt = dt[dt["productDescription"]=="API"]

    agg_functions = {
        'USD_per_KG': ['sum', 'mean', 'median', 'min', 'max'],
        'quantity_in_KG': ['sum', 'mean', 'median', 'min', 'max']
    }
    if by in "all year supplier customer ":
        if by == "all":
            resultDF = dt.groupby(['year', 'customerCountry', 'supplierCountry']).agg(agg_functions).round(2)
        elif by == "supplier":
            resultDF = dt.groupby(['year', 'supplierCountry']).agg(agg_functions).round(2)
        elif by == "customer":
            resultDF = dt.groupby(['year', 'customerCountry']).agg(agg_functions).round(2)
        elif by == "year":
            resultDF = dt.groupby(['year']).agg(agg_functions).round(2)
    else:
        print("by must equal one of: all, year, supplier, customer. year is the default value")
        return()
    return(resultDF)

df_all = getAPIdf(chosenAPI, data)
#%%
st.dataframe(df_all.head())

chosenStats = st.sidebar.selectbox("Choose Summary of Statistic", ["All", "by year only", "by selling country", "by customer country"])

#%%

graph_dt = df_all.groupby(['Date'])['quantity', 'totalValueInUsd',
       'quantity_in_KG', 'USD_per_KG'].mean().reset_index()



chart = alt.Chart(graph_dt).mark_line().encode(
    x = alt.X('Date:N', title="Quarter"),
    y = alt.Y('USD_per_KG:Q', title="USD")
).properties(title="Price per KG by Quarter")

st.altair_chart(chart, use_container_width=True)

st.subheader("Country Type = " + chosenStats)
if chosenStats == "All":
    df_out = getSummary(df_all, by="all")
elif chosenStats == "by year only":
    df_out = getSummary(df_all)
elif chosenStats == "by selling country":
    df_out = getSummary(df_all, by="supplier")
elif chosenStats == "by customer country":
    df_out = getSummary(df_all, by="customer")
st.dataframe(df_out)

#%%

if chosenStats != "by year only":
    map_dt = df_out.reset_index()
    map_dt.columns = ["_".join(i) for i in map_dt.columns]
    country_col = "supplierCountry_"
    if chosenStats == "by selling country" or chosenStats == "All" :
        country_col = "supplierCountry_"
        st.subheader('Supplier Country Total Volume (KG)')
    if chosenStats == "by customer country":
        country_col = "customerCountry_"
        st.subheader('Customer Country Total Volume (KG)')

    countries = st.multiselect(
        "Choose supply countries", list(set(list(map_dt[country_col].values)))
    )
    if not countries:
        st.error("Please select at least one country.")
    else:
        map_dt= map_dt.set_index(country_col)
        map_dt = map_dt.loc[countries]
        map_dt = map_dt.reset_index()
        chart = (
            alt.Chart(map_dt)
            .mark_line(point=True)
            .encode(
                x=alt.X("year_:N", title="YEAR"),
                y=alt.Y("quantity_in_KG_sum:Q", title="Total in KG"),
                color=country_col,
            )
        ).properties(title="TOTAL by Country")
        st.altair_chart(chart, use_container_width=True)

        graph_dt2 = df_all.groupby(['Date', 'supplierCountry'])['quantity', 'totalValueInUsd', 'quantity_in_KG', 'USD_per_KG'].mean().reset_index()
        graph_dt2 = graph_dt2.set_index('supplierCountry')


        graph_dt2 = graph_dt2.loc[countries]
        graph_dt2 = graph_dt2.reset_index()


        chart = alt.Chart(graph_dt2).mark_line(point=True).encode(
            x = alt.X('Date:N', title="Quarter"),
            y = alt.Y('USD_per_KG:Q', title="USD"),
            color = 'supplierCountry:N'
        
        ).properties(title="Price per KG by Quarter by country")
        st.altair_chart(chart, use_container_width=True)

##### Make map####


#%%
def getLongLat(_country_in, att):
    x = geo()
    try:
        if att == "long":
            cor = x.get_long(country_name=_country_in)

        elif att == "lat":
            cor = x.get_lat(country_name=_country_in)
    except:
        cor = np.nan
    
    return cor
#%%

geo_dt = df_all.groupby(['Date', 'supplierCountry','customerCountry'])[ 'quantity', 'totalValueInUsd', 'quantity_in_KG', 'USD_per_KG'].mean().reset_index()
#%%
getLongLat_vec = np.vectorize(getLongLat)

#%%
country_type = "Supply Country"
if country_type=="Customer Country":
    metric = "customerCountry"

    country_arr = np.array(list(set(list(geo_dt["customerCountry"].values))))
elif country_type == "Supply Country":
    metric = "supplierCountry"

    country_arr = np.array( list(set(list(geo_dt["supplierCountry"].values))) )

longitude = getLongLat_vec(np.array(country_arr), att="long")
latitude = getLongLat_vec(np.array(country_arr), att="lat")

country_loc_dict = {k:[] for k in country_arr}
for i, v in enumerate(country_arr):
    country_loc_dict[v] = [longitude[i], latitude[i]]

#%%


geo_map_dt = geo_dt.groupby(["Date",metric])[ 'quantity_in_KG'].mean().reset_index()
country_arr_  = geo_map_dt[metric].values

geo_map_dt["longitude"] = [country_loc_dict[i][0] for i in country_arr_]

geo_map_dt["latitude"] = [country_loc_dict[i][1] for i in country_arr_]

geo_map_dt = geo_map_dt.dropna(axis=0)

#%%
def min_max_normalize(array_in):
    max_val = np.max(array_in)
    min_val = np.min(array_in)
    normalized_ = [((i - min_val)*1000)/(max_val-min_val) for i in array_in]
    return np.array(normalized_)
#%%
geo_map_dt["norm_quan_by_KG"] = min_max_normalize(geo_map_dt["quantity_in_KG"].values)
#%%
###### RAZZLE DAZZLE####
########################################################################################
## MAP
if st.button("See total global export in kg"):
    
    # Set viewport for the deckgl map
    view = pdk.ViewState(latitude=0, longitude=0, zoom=0.9,)

    # Create the scatter plot layer
    kgLayer = pdk.Layer(
            "ScatterplotLayer",
            data=geo_map_dt,
            pickable=False,
            opacity=0.25,
            stroked=True,
            filled=True,
            radius_scale=5000,
            radius_min_pixels=15,
            radius_max_pixels=1000000000000,
            line_width_min_pixels=1,
            get_position=["longitude", "latitude"],
            get_radius= ["norm_quan_by_KG"],
            get_fill_color=[180, 0, 200, 140],
            get_line_color=[255,0,0],
            tooltip="test test",
        )



    # Create the deck.gl map
    r = pdk.Deck(
        layers=[kgLayer],
        initial_view_state=view,
        map_style="mapbox://styles/mapbox/light-v10",
    )


    # Create a subheading to display current date
    subheading = st.subheader("")

    # Render the deck.gl map in the Streamlit app as a Pydeck chart 
    map = st.pydeck_chart(r)

    # Update the maps and the subheading each day for 90 days
    dates = sorted(list(set(geo_map_dt["Date"].values)))
    # datetimes = [datetime.strptime(i, "%Y-%m-%d") for i in dates]
    # datetimes_slide = st.slider("Select Date", datetimes[0], datetimes[-1], )

    for date in dates:

        # Update data in map layers
        kgLayer.data = geo_map_dt[geo_map_dt['Date'] == date]

        # Update the deck.gl map
        r.update()

        # Render the map
        map.pydeck_chart(r)

        # Update the heading with current date
        subheading.subheader("%s on : %s" % ("Quantity Exported in KG by Quarter", date))

        time.sleep(0.5)
