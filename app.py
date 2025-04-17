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
from authentication import auth_section, protected_route
from optimization import identify_available_space, suggest_placement_in_available_space
from visualization import visualize_room_with_available_spaces
# cred = credentials.Certificate("firebase_credentials.json") 

import psycopg2
from dotenv import load_dotenv
import os
from st_supabase_connection import SupabaseConnection
from supabase import create_client, Client
# Load environment variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
import streamlit as st
from st_supabase_connection import SupabaseConnection


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Connect to the database
try:
    # Initialize connection.
    connection = st.connection("supabase",type=SupabaseConnection)
    # Example: Query data
    response = connection.table("reviews").select("*").execute()
    data = response.data
    print("Connection successful!")
    
except Exception as e:
    print(f"Failed to connect: {e}")

# authentication
# Get token and store in session_state
access_token = auth_section(supabase)
if access_token:
    st.session_state['access_token'] = access_token



# Helper: get user-bound supabase client
from supabase import create_client, Client

def get_user_supabase():
    token = st.session_state.get('access_token')
    if token:
        return create_client(st.secrets['SUPABASE_URL'], token)
    return supabase  # fallbottom to anon/service

# Function to Save Data to Firebase
def save_data(room_sizes, positions, doors, review, is_enough_path, space, overall, is_everything):
    if not st.session_state.auth.get('user'):
        st.error("Please sign in to submit reviews")
        return
    try:
        objects = []
        objects_positions = []
        for position in positions:
            print(position)
            if isinstance(position, (list, tuple)) and len(position) >= 8:
                objects.append({
                    "name": position[5],
                    "width": position[2],
                    "depth": position[3],
                    "height": position[4]
                })
                objects_positions.append({
                    "x": position[0],
                    "y": position[1],
                    "must_be_corner": position[6],
                    "against_wall": position[7]
                })

        # Convert input data to match table schema
        review_data = {
            "room_width": int(room_sizes[0]),
            "room_depth": int(room_sizes[1]),
            "room_height": int(room_sizes[2]),  # Assuming 3rd value exists
            "objects": objects,
            "objects_positions": objects_positions,
            "review": {
                "text": review,
            },
            "doors_windows": [{
                "type": door[1],
                "position": {"x": door[2], "y": door[3]},
                "dimensions": {"width": door[4], "height": door[5]}
            } for door in doors],
            "user_id": st.session_state.user.id
        }

        # Add optional fields if available
        if is_enough_path and space and overall:
            review_data.update({
                "is_enough_path": is_enough_path,
                "space": space,
                "overall": overall,
                "is_everything": is_everything,
            })
        # Insert into Supabase
        response = supabase.table('reviews').insert(review_data).execute()
        if response.data:
            st.success("Review saved successfully!")
            return None
        else:
            st.error("Failed to save review")
            return None
    except Exception as e:
        st.error(f"Error saving review: {str(e)}")
        return None




OBJECT_TYPES = []
with open('object_types.json') as f:
    OBJECT_TYPES = json.load(f)
    
if not st.session_state.auth.get('user'):
    st.warning("Please sign in to access this page")
    
else:
    # get root path
    # Streamlit App Title
    st.title("Floorplan Generator and Visualizer")
    st.write("This app generates a floorplan and visualizes it in 3D.")

    door_images = { 
        "top" : "front.png",
        "left" : "left.png",
        "right" : "right.png",
        "bottom" : "back.png", 
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
        room_height = st.number_input("Enter room height :", min_value=100, value=280)

        # Dropdown Menu for Object Selection
        objects = ["Bathtub", "Sink", "Washing Machine", "Toilet", "Shower","Double Sink", "Cabinet" ]
        selected_object = st.multiselect("Select Objects:", objects)

        # Dropdown Menu for Room Selection
        rooms = [ "Bathroom"]
        selected_room = st.selectbox("Select a Room type:", rooms)

        door_type= ["top", "bottom", "right","left"]
        # add gap between the two columns
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        
        # Number Inputs
        x = st.number_input("Enter door distance from the corner (X):", min_value=1, value=50)
        y = 0
        door_type= ["top", "bottom", "right","left"]
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
    isTrue = False

    positions = []
    # Generate Button for 3D Visualization
    if st.button("Generate 3D Plot"):
        if selected_door_type == "top":
            y = x
            x = 0
            if x+door_width > room_depth:
                x = room_depth - door_width
        if selected_door_type == "bottom":
            y = x
            x = room_width
            if x+door_width > room_depth:
                x = room_depth - door_width
        if selected_door_type == "right":
            y = room_depth 
            if y+door_width > room_width:
                y = room_width - door_width
        if selected_door_type == "left":
            if y+door_width > room_width:
                y = room_width - door_width
        selected_objects = [objects_map[obj] for obj in selected_object]
   
        windows_doors = [
            ("door1", selected_door_type, x, y, door_width, door_height, 0),
        ]
        bathroom_size = ( room_width,room_depth)  # Width, Depth, Height

        positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES,attempt=10000)



        
        placed_objects = [pos[5] for pos in positions]
        i = 1
        while len(placed_objects) < len(selected_objects) and i < 3:
            positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES,attempt=10000)
            placed_objects = [pos[5] for pos in positions]
            i += 1
            


        # Find available spaces (excluding shadows by default)
        available_spaces = identify_available_space(positions, (room_width, room_depth), grid_size=1)

        # Print the available spaces
        print(f"Found {len(available_spaces)} available spaces:")
        for i, space in enumerate(available_spaces):
            x, y, width, depth = space
            print(f"Space {i+1}: Position ({x}, {y}), Size: {width}x{depth} cm")

        
        # ### Try to place a new toilet in an available space
        # suggested_placement = suggest_placement_in_available_space(
        #     available_spaces, 
        #     "Toilet", 
        #     OBJECT_TYPES
        # )

        # if suggested_placement:
        #     x, y, width, depth = suggested_placement
        #     print(f"Suggested toilet placement: Position ({x}, {y}), Size: {width}x{depth} cm")
            
        #     # You could then add this to your placed_objects list
        #     # (You'd need to add height and shadow values based on your object types)
        #     height =  OBJECT_TYPES["toilet"]["optimal_size"][2]
        #     shadow = OBJECT_TYPES["toilet"]["shadow_space"] # Example shadow values
        #     new_object = (x, y, width, depth, height, 0, 0, 0, shadow)
        #     placed_objects.append(new_object)
        #     positions.append(new_object)

        # else:
        #     print("No suitable space found for a toilet")

        ###





        # visualization
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
        st.session_state.positions = positions
        st.session_state.windows_doors = windows_doors
        st.session_state.fig = fig
        st.session_state.fig2 = fig2
        st.session_state.isTrue = isTrue
        st.session_state.positions = positions
        st.session_state.windows_doors = windows_doors
        figvis = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces)
        st.pyplot(figvis)
        st.session_state.figvis = figvis
    
    elif st.session_state.fig and st.session_state.fig2:
        st.pyplot(st.session_state.fig)
        st.pyplot(st.session_state.fig2)
        st.pyplot(st.session_state.figvis)





    is_enough_path = st.checkbox("Is there enough pathway space?")
    is_everything = st.checkbox("Is everything placed?")
    space = st.slider("Space Utilization", 0,10,5)
    overall = st.slider("Overall Satisfaction", 0,10,5)
    st.write("Write your review about the generated room:")
    review = st.text_area("Review", "Write your review here...")
    if st.button("Submit Review"):
        save_data((room_width, room_depth, room_height), st.session_state.positions, st.session_state.windows_doors, review, is_enough_path, space, overall, is_everything)
        st.success("Thank you for your review, all data saved to database!")
        


    
# TODO bottom door cant work
# TODO Too much conversion of the objectss