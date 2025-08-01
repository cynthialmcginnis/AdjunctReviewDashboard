#!/usr/bin/env python
# coding: utf-8

# In[19]:

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from PIL import Image

# --- App Config ---
st.set_page_config(page_title="Adjunct Review Dashboard", layout="wide")

# --- Banner Image ---
img_path = "/Users/cynthiamcginnis/Downloads/openart-image_TJPSjReV_1750140876229_raw.png"
if os.path.exists(img_path):
    image = Image.open(img_path)
    resized_image = image.resize((250, 250))  # Adjust width and height
    st.image(resized_image)

# --- Title & Description ---
st.title("🎓 Adjunct Faculty Review Dashboard")
st.markdown("""
Welcome to the **Adjunct Review Tracker**. Upload your **Faculty list** and **Visit records** Excel files to:
- Match current adjuncts across records
- See who has **never been visited**, **needs a visit**, or is **up to date**
- Filter by region and explore status using a pie chart and interactive table.
""")

# --- File Uploads ---
st.sidebar.header("📁 Upload Files")
faculty_file = st.sidebar.file_uploader("Upload Faculty Excel File", type=["xlsx"])
visit_file = st.sidebar.file_uploader("Upload Visit Excel File", type=["xlsx"])

# --- UI Padding Separator ---
st.sidebar.markdown("---")

# --- Region Filter (dropdown updates dynamically later) ---
selected_region = st.sidebar.selectbox("🌍 Filter by Region (after file upload)", options=["All"], disabled=True)

if faculty_file and visit_file:
    # --- Load Faculty Data ---
    faculty_df = pd.read_excel(faculty_file)
    adjunct_df = faculty_df[faculty_df['Business Title'].str.contains("Adjunct", case=False, na=False)].copy()

    # --- Load and Combine Visit Records from All Sheets ---
    all_sheets = pd.read_excel(visit_file, sheet_name=None)
    visits = pd.concat(all_sheets.values(), ignore_index=True)

    # --- Clean Visit Data ---
    visits = visits.rename(columns=lambda x: x.strip())
    visits = visits.dropna(subset=['Last Name', 'First Name'])

    # --- Merge Data ---
    merged = adjunct_df.merge(visits, how="left", on=["First Name", "Last Name"], suffixes=("", "_visit"))
    merged["Visit Date"] = pd.to_datetime(merged["LEO Visit Date"], errors="coerce")
    merged["Last Visit"] = merged.groupby(['First Name', 'Last Name'])['Visit Date'].transform('max')

    # --- Define Visit Status ---
    def determine_status(date):
        if pd.isna(date):
            return "Never Visited"
        elif pd.Timestamp.now() - date > pd.Timedelta(days=365):
            return "Needs Visit"
        else:
            return "Up to Date"

    merged["Visit Status"] = merged["Last Visit"].apply(determine_status)

    # --- Final Columns ---
    final_df = merged[["First Name", "Last Name", "Business Title", "Region", "Last Visit", "Visit Status"]].drop_duplicates()
    final_df["Last Visit"] = final_df["Last Visit"].dt.date

    # --- Region Filter ---
    regions = ["All"] + sorted(final_df["Region"].dropna().unique().tolist())
    selected_region = st.sidebar.selectbox("🌍 Filter by Region", options=regions)
    if selected_region != "All":
        final_df = final_df[final_df["Region"] == selected_region]

    # --- Status Table ---
    st.subheader("📋 Adjunct Visit Table")
    st.dataframe(final_df, use_container_width=True)

    # --- Pie Chart ---
    st.subheader("📊 Visit Status Overview")
    fig, ax = plt.subplots(figsize=(5, 5))
    status_counts = final_df["Visit Status"].value_counts()
    ax.pie(status_counts, labels=status_counts.index, autopct="%1.1f%%", startangle=90,
           colors=["#28a745", "#ffc107", "#dc3545"])
    ax.axis("equal")
    st.pyplot(fig)
    
    # ✅ Download Button
    csv = final_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Visit Status as CSV",
        data=csv,
        file_name="adjunct_visit_status.csv",
        mime="text/csv"
    )

else:
    st.info("Please upload both a Faculty Excel file and a Visit Record Excel file from LEO.")

# In[ ]:




