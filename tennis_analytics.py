import streamlit as st
import pandas as pd
import mysql.connector

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Dhinesh@0512",
    database="TENNIS_DATABASE"
)

# Helper function to load data
def load_table(query):
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return pd.DataFrame(result, columns=columns)

# Load tables
categories_df = load_table("SELECT * FROM Categories")
competitions_df = load_table("SELECT * FROM Competitions")
complexes_df = load_table("SELECT * FROM Complexes")
venues_df = load_table("SELECT * FROM Venues")
competitors_df = load_table("SELECT * FROM Competitors")
rankings_df = load_table("SELECT * FROM Competitor_Rankings")

# Merge competitor with ranking
competitor_data = pd.merge(competitors_df, rankings_df, on="Competitor Id", how="left")

st.set_page_config(page_title="Tennis Dashboard", layout="wide")
st.title("🎾 Tennis Insights Dashboard")

# Tabs for navigation
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏠 Home", "🔍 Search Competitors", "📊 Competitor Detail",
    "🌍 Country Insights", "🏆 Leaderboards",
    "🏟️ Venues & Complexes", "👤 Creator Info"
])

# 1. Homepage Dashboard
with tab1:
    st.header("Dashboard Overview")

    total_competitions = len(competitions_df)
    total_categories = len(categories_df)
    total_venues = len(venues_df)
    total_complexes = len(complexes_df)
    total_competitors = len(competitors_df)
    total_countries = competitors_df['Country'].nunique()
    max_points = rankings_df['Points'].max()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Competitions", total_competitions)
    col1.metric("Total Categories", total_categories)
    col2.metric("Venues", total_venues)
    col2.metric("Complexes", total_complexes)
    col3.metric("Competitors", total_competitors)
    col3.metric("Countries", total_countries)
    st.metric("Highest Points", max_points)

# 2. Search & Filter
with tab2:
    st.header("Search & Filter Competitors")

    name_query = st.text_input("Search by Name")
    country_filter = st.selectbox("Filter by Country", ["All"] + sorted(competitors_df['Country'].dropna().unique()))
    min_rank, max_rank = st.slider("Rank Range", 1, int(rankings_df['Rank'].max()), (1, 100))
    min_points, max_points = st.slider("Points Range", 0, int(rankings_df['Points'].max()), (0, 5000))

    name_mask = competitor_data['Name'].str.contains(name_query, case=False, na=False)
    country_mask = (
        competitor_data['Country'] == country_filter
        if country_filter != "All"
        else pd.Series([True] * len(competitor_data))
    )
    rank_mask = competitor_data['Rank'].between(min_rank, max_rank)
    points_mask = competitor_data['Points'].between(min_points, max_points)

    filtered = competitor_data[name_mask & country_mask & rank_mask & points_mask]

    st.dataframe(filtered[['Name', 'Rank', 'Country', 'Points']])

# 3. Competitor Detail Viewer
with tab3:
    st.header("Competitor Details")
    selected_name = st.selectbox("Select a Competitor", sorted(competitor_data['Name']))
    selected = competitor_data[competitor_data['Name'] == selected_name].iloc[0]

    st.subheader(f"{selected['Name']} ({selected['Abbreviation']})")
    st.write(f"**Country**: {selected['Country']}")
    st.write(f"**Rank**: {selected['Rank']} ({'+' if selected['Movement'] > 0 else ''}{selected['Movement']})")
    st.write(f"**Points**: {selected['Points']}")
    st.write(f"**Competitions Played**: {selected['Competitions Played']}")

# 4. Country-Wise Insights
with tab4:
    st.header("Country Insights")
    country_summary = competitor_data.groupby("Country").agg({
        "Competitor Id": "count",
        "Points": ["mean", "sum"]
    }).reset_index()
    country_summary.columns = ["Country", "Competitors", "Avg Points", "Total Points"]
    st.bar_chart(country_summary.set_index("Country")["Competitors"])

# 5. Leaderboards
with tab5:
    st.header("Leaderboards")
    option = st.selectbox("View", ["Top 10 by Rank", "Top by Points", "Stable Rankers (No Movement)"])

    if option == "Top 10 by Rank":
        st.dataframe(competitor_data.nsmallest(10, "Rank")[['Name', 'Rank', 'Points']])
    elif option == "Top by Points":
        st.dataframe(competitor_data.nlargest(10, "Points")[['Name', 'Points', 'Rank']])
    else:
        stable = competitor_data[competitor_data["Movement"] == 0]
        st.dataframe(stable[['Name', 'Rank', 'Points']])

# 6. Venue & Complex Viewer
with tab6:
    st.header("Venues & Complexes")
    merged = venues_df.merge(complexes_df, on="Complex Id")
    filter_country = st.selectbox("Country Name", ["All"] + sorted(merged['Country Name'].unique()))
    if filter_country != "All":
        merged = merged[merged["Country Name"] == filter_country]
    st.dataframe(merged[["Venue Name", "Complex Name", "City Name", "Country Name"]])
    venue_count = merged["Complex Name"].value_counts().reset_index()
    venue_count.columns = ["Complex", "Venue Count"]
    st.bar_chart(venue_count.set_index("Complex"))

# 7: Creator Info
with tab7:
    st.header("Creator of this Project")
    st.markdown("""
    **App Name:** Sports Analytics Dashboard  
    **Creator:** DHINESH KUMAR KANNAN
    """)
