import streamlit as st
from pymongo import MongoClient
import google.generativeai as genai
import pandas as pd
import os

# Configuration
# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "cooking_assistant"
COLLECTION_NAME = "user_preferences"

# Gemini SDK Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
preferences_collection = db[COLLECTION_NAME]

# Streamlit App
st.title("AI-Powered Cooking Assistant")
st.write(
    "Welcome to your AI Cooking Assistant! Get personalized recipes, step-by-step instructions, "
    "and meal planning support. Input your ingredients and preferences to get started."
)

# Sidebar for user inputs
with st.sidebar:
    st.header("Your Preferences")
    ingredients = st.text_area(
        "Available Ingredients (comma-separated)",
        placeholder="e.g., tomatoes, chicken, onions",
    )
    dietary_preferences = st.text_input(
        "Dietary Preferences", placeholder="e.g., vegan, gluten-free"
    )
    cuisine_type = st.selectbox(
        "Preferred Cuisine", ["Any", "Italian", "Chinese", "Indian", "Mexican", "French"]
    )
    submit_button = st.button("Get Recipe")

# Main Section
if submit_button:
    if not ingredients:
        st.error("Please enter at least one ingredient.")
    else:
        # Prepare the user input
        ingredients_list = [ingredient.strip() for ingredient in ingredients.split(",")]
        cuisine_prompt = f"cuisine: {cuisine_type}" if cuisine_type != "Any" else ""
        prompt = (
            f"Suggest a recipe only based on these ingredients: {', '.join(ingredients_list)}. "
            f"Consider dietary preferences: {dietary_preferences}. {cuisine_prompt}."
        )
        st.write("Fetching personalized recipe...")

        try:
            # Call Gemini API to generate content
            response = model.generate_content(prompt)
            recipe_text = response.text.strip()

            if recipe_text:
                st.subheader("Your Recipe")
                st.write(recipe_text)

                # Save preferences to MongoDB
                preferences_collection.insert_one(
                    {
                        "ingredients": ingredients_list,
                        "dietary_preferences": dietary_preferences,
                        "cuisine_type": cuisine_type,
                        "recipe_text": recipe_text,
                        "timestamp": pd.Timestamp.now(),
                    }
                )
                st.success("Recipe and preferences saved!")
            else:
                st.error("No recipe could be generated. Try refining your inputs.")

        except Exception as e:
            st.error(f"Error generating recipe: {e}")

# Display saved preferences
st.header("Your Saved Preferences")
saved_preferences = list(preferences_collection.find().sort("timestamp", -1))
if len(saved_preferences) > 0:
    for pref in saved_preferences:
        st.write(f"**Date:** {pref['timestamp']}")
        st.write(f"**Ingredients:** {', '.join(pref['ingredients'])}")
        st.write(f"**Dietary Preferences:** {pref['dietary_preferences']}")
        st.write(f"**Cuisine Type:** {pref['cuisine_type']}")
        st.write(f"**Last Recipe:** {pref['recipe_text']}")
        st.write("---")
else:
    st.write("No saved preferences yet.")
