import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from generate_room import fit_objects_in_room
from visualization import visualize_room_with_shadows_3d, draw_2d_floorplan
from utils import check_valid_room
import json
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("firebase_credentials.json") 

import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Connect to the database
try:
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    print("Connection successful!")
    
    # Create a cursor to execute SQL queries
    cursor = connection.cursor()
    
    # Example query
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print("Current Time:", result)

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("Connection closed.")

except Exception as e:
    print(f"Failed to connect: {e}")

# Function to Save Data to Firebase
def save_data(room_sizes, positions, doors, review):
    try:
        ref = db.reference("/floorplans")  # Store all floorplans here

        # Save room sizes
        width, depth = room_sizes
        room_data = {
            "room_width": width,
            "room_depth": depth
        }
        room_ref = ref.push(room_data)  # Create a new floorplan entry

        # Save doors under the floorplan
        doors_ref = room_ref.child("doors")
        for door in doors:
            door_name, door_type, x, y, door_width, door_height = door
            door_data = {
                "door_name": door_name,
                "door_type": door_type,
                "x": x,
                "y": y,
                "door_width": door_width,
                "door_height": door_height
            }
            doors_ref.push(door_data)  # Store doors separately

        # Save objects under the floorplan
        objects_ref = room_ref.child("objects")
        
        for obj in positions:
            x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
            object_data = {
                "object": name,
                "x": x,
                "y": y,
                "width": width,
                "depth": depth,
                "height": height,
                "shadow": shadow,
                "must_be_corner": must_be_corner,
                "must_be_against_wall": must_be_against_wall
            }
            objects_ref.push(object_data)  # Store objects separately

        # Save review under the floorplan
        #review_ref = room_ref.child("review")
        #review_data = {
        #    "review": review
        #}
        #review_ref.push(review_data)  # Store review separately

        print("✅ Data saved successfully!")
    except Exception as e:
        print(f"❌ Error saving data: {str(e)}")




OBJECT_TYPES = []
with open('object_types.json') as f:
    OBJECT_TYPES = json.load(f)
    
# get root path
# Streamlit App Title
st.title("Floorplan Generator and Visualizer")
st.write("This app generates a floorplan and visualizes it in 3D.")

door_images = { 
    "front" : "front.png",
    "left" : "left.png",
    "right" : "right.png",
    "back" : "back.png", 
}

objects_map = { 
    "Bathtub": "bathtub",
    "Sink": "sink",
    "Washing Machine": "washing_machine",
    "Toilet": "toilet",
    "Shower": "shower",
    "Double Sink": "double_sink",
    "Cabinet": "cabinet",
}


# Layout with Columns
col1, col2 = st.columns([1, 1])  # Create two equal-width columns

with col1:    
    # Number Inputs
    room_width = st.number_input("Enter room width :", min_value=50, value=200)
    room_depth = st.number_input("Enter room depth :", min_value=50, value=200)
    # Dropdown Menu for Object Selection
    objects = ["Bathtub", "Sink", "Washing Machine", "Toilet", "Shower","Double Sink", "Cabinet" ]
    selected_object = st.multiselect("Select Objects:", objects)

    # Dropdown Menu for Room Selection
    rooms = [ "Bathroom"]
    selected_room = st.selectbox("Select a Room type:", rooms)

    door_type= ["front", "back", "right","left"]
    # add gap between the two columns
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    
    # Number Inputs
    x = st.number_input("Enter door distance from the corner (X):", min_value=1, value=1)
    y = 0
    door_type= ["front", "back", "right","left"]
    selected_door_type = st.selectbox("Select door type:", door_type)
    door_width = st.number_input("Enter Door Width:", min_value=1, value=75)
    door_height = st.number_input("Enter Door Height:", min_value=1, value=200)
    
    door = ["Inward", "Outward"]
    selected_door_way = st.selectbox("Door type:", door)



with col2:
    
    image_path = "room.png"
    st.image(image_path, caption=f"Door sizes ", use_column_width=True)
    # Display Image Dynamically Based on Selection
    image_path = door_images.get(selected_door_type, "default.png")
    st.image(image_path, caption=f"Selected door position: {selected_door_type}", use_column_width=True)
windows_doors = []

positions = []
# Generate Button for 3D Visualization
if st.button("Generate 3D Plot"):
    if selected_door_type == "front" or selected_door_type == "back":
        y = x
        x = 0
    selected_objects = [objects_map[obj] for obj in selected_object]

    windows_doors = [
        ("door1", selected_door_type, x, y, door_width, door_height, 0),
    ]
    bathroom_size = ( room_width,room_depth)  # Width, Depth, Height

    positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES,attempt=10000)
    fig = visualize_room_with_shadows_3d(bathroom_size, positions, windows_doors)
    isTrue = check_valid_room( positions)
    if isTrue == True:
        st.success("The room is valid.")
    else:
        st.error("The room is invalid.")
    # Show the plot in Streamlit
    st.pyplot(fig)
    fig2 = draw_2d_floorplan(bathroom_size, positions, windows_doors, selected_door_way)
    st.pyplot(fig2)



# add string to show the objects position in the room
st.write("Objects position in the room:")

for x,y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow in positions:
    st.write(f"Object: {name}")
    st.write(f"Position: {x}, {y}, ")
    st.write(f"Size: {width}, {depth}, ")
    st.write(f"Height: {height} ,")
    st.write(f"Must be corner: {must_be_corner}, Must be against wall: {must_be_against_wall}")



# add a section which is enable to write a review about the app
st.write("Write your review about the generated room:")
review = st.text_area("Review", "Write your review here...")
if st.button("Submit Review"):
    save_data((room_width, room_depth), positions, windows_doors, review)
    st.success("Thank you for your review, all data saved to database!")
    


    
# TODO Back door cant work
# TODO Too much conversion of the objects