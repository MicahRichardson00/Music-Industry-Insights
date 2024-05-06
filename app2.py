import altair as alt
import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import geopandas as gpd
import folium
from streamlit_folium import folium_static

st.set_page_config(layout="centered")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Music Consumption", "Streaming Platforms Overview","Top Genres by State","Consumption by Generation","Definitions"])

with tab1:
    @st.cache_data
    def load_data(xlsx):
        df = pd.read_excel(xlsx)
        return df
    @st.cache_data
    def load_csv(csv):
        df2 = pd.read_csv(csv)
        return df2
    st.title('45 Years of Music Consumption Sales by Format')
    df = load_csv("data2/US Recorded Music Revenues by Format.csv")

    format_choice = st.selectbox("Select Format", options=df['Format'].unique())
    revenue_type = st.radio("Select Revenue Type", ("Revenue", "Revenue (Inflation Adjusted)"))
    filtered_data = df[df['Format'] == format_choice]

    years = filtered_data['Year'].unique()
    years.sort()

    start_year, end_year = st.select_slider(
        'Select a range of years',
        options=years,
        value=(years[0], years[-1]))

    filtered_data = filtered_data[(filtered_data['Year'] >= start_year) & (filtered_data['Year'] <= end_year)]

    fig = px.bar(filtered_data, x='Year', y=revenue_type, title=f"{revenue_type} over Years for {format_choice}",color_discrete_sequence=['#800020'])
    st.plotly_chart(fig)


    st.header("Industry Music Consumption Methods by Genre")
    t_genres = load_data('data2/FormatXGenre_updated.xlsx')
    t_genres = t_genres.iloc[:59]
    genre_select = st.selectbox('Select a genre:', t_genres['Genre'].unique())
    filtered_data2 = t_genres[t_genres['Genre'] == genre_select]

    chart2 = alt.Chart(filtered_data2).mark_bar(color='#800020').encode(
        x=alt.X('Music Format:N', axis=alt.Axis(title='Music Format', labelAngle=0)),
        y=alt.Y('Value:Q', axis=alt.Axis(title='Percentage', format='.1%')),
        tooltip=['Music Format', alt.Tooltip('Value:Q', title='Percentage', format='.1%')]).properties(
        title=f'Music Consumption Format for {genre_select}')
    st.altair_chart(chart2, use_container_width=True)

with tab2:
    st.header('Music Streaming Market Share Percentage by Platform')
    marketshare = load_data('data2/MusicMarketShare.xlsx')
    marketshare['Music Industry Market Share'] *= 100
    marketshare['Music Industry Market Share'] = marketshare['Music Industry Market Share'].round(1)
    adjustments = {13.3: -0.2, 13.4: 3.0, 13.7: 5.2}
    marketshare['Adjusted Market Share'] = marketshare['Music Industry Market Share'].apply(lambda x: x + adjustments.get(x, 0))

    fig = px.scatter(
        marketshare,
        x="Adjusted Market Share", 
        y="Music Industry Market Share",  
        size="Music Industry Market Share",
        color="Streaming Platform", 
        hover_name="Streaming Platform", 
        text=marketshare['Music Industry Market Share'].apply(lambda x: f"{x}%"), 
        size_max=100,
        template='plotly_white')

    fig.update_traces(
        textfont=dict(
            size=12,
            color='black',
            family='Arial, sans-serif'
        ),
        texttemplate='%{text}',
        hovertemplate='<b>%{hovertext}</b><br>Market Share: <b>%{text}</b>')
    fig.update_layout(
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        xaxis_title='',
        yaxis_title='')
    st.plotly_chart(fig)
    
    st.header('Top 4 U.S. Based Streaming Platforms, Most Streamed Genres')
    plat_genre = load_data('data2/PlatformGenres.xlsx')
    
    def color_genre(val):
        colors = {
            'Pop': 'background-color: lightblue',
            'Rap/Hip-Hop': 'background-color: lightcoral',
            'Rock': 'background-color: lightgreen',
            'Country': 'background-color: lightyellow',
            'Latin': 'background-color: lightgrey'}
        return colors.get(val, '')
    plat_genre.reset_index(drop=True, inplace=True)
    st.dataframe(plat_genre.style.applymap(color_genre))

with tab3:
    st.header('Top 4 Most Popular Music Genres in the U.S. by State')
    col_1, col_2 = st.columns([1, 1])
    df3 = load_data('data2/2022_StateGenre_Top4_2.xlsx')

    with col_1:
        st.markdown("# Select Rank")
        rank_selection = st.radio("", df3['Ranking'].unique())
    with col_2:
        st.write("# Genre Legend")
        st.markdown("""
            <span style='color: orange;'>**Country**: Orange</span><br>
            <span style='color: black;'>**Rap/Hip Hop**: Black</span><br>
            <span style='color: red;'>**Rock**: Red</span><br>
            <span style='color: green;'>**Pop**: Green</span><br>
            <span style='color: blue;'>**Rhythm and Blues**: Blue</span><br>
            <span style='color: purple;'>**EDM**: Purple</span><br>
            """, unsafe_allow_html=True)
    filtered_df = df3[df3['Ranking'] == rank_selection]

    my_USA_map = gpd.read_file('data2/cb_2018_us_state_500k.shp')
    territory_indices = [45, 37, 38, 44, 13] 
    my_USA_map = my_USA_map.drop(territory_indices)

    gdf = my_USA_map.merge(filtered_df, left_on='NAME', right_on='State')  
    m = folium.Map(location=[37, -102], zoom_start=4)

    def assign_color(genre):
        color_map = {
            'Country': 'orange',
            'Rap/Hip Hop': 'black',
            'Rock': 'red',
            'Pop': 'green',
            'Rhythm and Blues': 'blue',
            'EDM': 'purple'
        }
        return color_map.get(genre, 'gray')  # Default to gray if genre not listed

    gdf['color'] = gdf['Genre'].apply(assign_color)

    geojson_data = gdf.to_json()
    folium.GeoJson(
        geojson_data,
        style_function=lambda feature: {
            'fillColor': feature['properties']['color'],
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.7
        },
        tooltip=folium.GeoJsonTooltip(fields=['NAME', 'Genre'],
                                    aliases=['State', 'Genre'],
                                    localize=True)
    ).add_to(m)

    folium_static(m)

with tab4:
    col_10, col_20 = st.columns([1, 2])
    age_pref = load_data('data2/AgeGroupPreferences.xlsx')
    with col_10:
        age_group = st.radio("Select an Age Group:", age_pref['Age Group'].tolist())
    selected_data = age_pref[age_pref['Age Group'] == age_group]
    with col_20:
        st.markdown(f"""
        ### Preferences for Age Group: {age_group}
        1. Most Popular Genre: **{selected_data.iloc[0]['Most Popular Genre']}**
        2. Second Most Popular Genre: **{selected_data.iloc[0]['Second Most Popular Genre']}**
        3. Third Most Popular Genre: **{selected_data.iloc[0]['Third Most Popular Genre']}**""")
    st.write('\n' * 2)
    st.header("How Does Each Generation Consume Music?")

    age_genres = load_data('data2/Transformed_Music_Consumer_2022.xlsx')
    sub_age_df = age_genres[age_genres['Age Group'].isin(['Gen Z (13-28)', 'Gen X (44-57)','Millennials (29-43)','Baby Boomers (58-77)'])]
    
    generation_select = st.selectbox('Select a listening method:', sub_age_df['Category'].unique())

    filtered_data3 = sub_age_df[sub_age_df['Category'] == generation_select]

    chart3 = alt.Chart(filtered_data3).mark_bar(color='#800020').encode(
        x=alt.X('Age Group:N', axis=alt.Axis(title='Age Group', labelAngle=0)),
        y=alt.Y('Value:Q', axis=alt.Axis(title='Percentage', format='.1%')),
        tooltip=['Age Group', alt.Tooltip('Value:Q', title='Percentage', format='.1%')]
    ).properties(
        title=f'Music Consumption Format for {generation_select}')
    st.altair_chart(chart3, use_container_width=True)
    
with tab5:
    definitions = {
    "Music Streamer": "Listened to music via free/paid online radio or on-demand services in the past year (i.e., Pandora, Spotify, YouTube).",
    "Free Streamer": "Stream music but did not use a paid subscription service.",
    "Paid Subscriber": "Personally paid for an on-demand music subscription service (not including Amazon Prime subscriptions).",
    "Music Buyer": "Purchased at least one CD, digital track/album, vinyl record or paid to listen to online radio or on-demand music services in the past year.",
    "CD Buyer": "Purchased at least one full/single CD in the past year.",
    "Digital Buyer": "Purchased at least one digital track/album in the past year.",
    "Vinyl Buyer": "Purchased at least one new vinyl album in the past year.",
    "P2P Downloader": "Downloaded at least one track for free from a file-sharing service in the past year.",
    "Digital Streams": "Refers to accessing music through online streaming services that provide either free or subscription-based listening without the need to download.",
    "Digital Download": "Involves purchasing and downloading music from online platforms such as iTunes or Amazon Music.",
    "Use Social Media For Music": "Follows, likes, shares or listens to music or artist on social media platforms."}

    st.title("Music Consumption Definitions")
    st.write("Click a button to Show/Hide a definition")

    for term, definition in definitions.items():
        if st.button(f'{term}'):
            with st.expander("Definition", expanded=True):
                st.write(definition)

    links_md = """
    - [U.S. Music Revenue Database - RIAA - Big music dataset](https://www.riaa.com/u-s-sales-database/)
    - [MW_Table_033123a.pdf (riaa.com) - Age Demographics from RIAA](https://www.riaa.com/wp-content/uploads/2023/05/MW_Table_033123a.pdf)
    - [40 Years of Music Industry Sales (kaggle.com) - Channels of Music Sales](https://www.kaggle.com/datasets/imtkaggleteam/40-years-of-music-industry-sales)
    - [Favorite Music by State - Wisevoter - Favorite Genres By State](https://wisevoter.com/report/favorite-music-genre-by-state/)
    """
    st.title("Sources")
    st.markdown(links_md)