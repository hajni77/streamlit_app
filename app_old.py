import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from generate_room import fit_objects_in_room
from visualization import visualize_room_with_shadows_3d, draw_2d_floorplan
from utils import check_valid_room, check_overlap
import json
import firebase_admin
from firebase_admin import credentials, db
from authentication import auth_section, protected_route
from optimization import identify_available_space, suggest_placement_in_available_space, add_objects_to_available_spaces, suggest_additional_fixtures, switch_objects
from visualization import visualize_room_with_available_spaces
from optimization import evaluate_room_layout, mark_inaccessible_spaces
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
st.set_page_config(page_title="Floorplan Generator and Visualizer", page_icon=":house:")
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

common_fixtures = [
        "Toilet", "Sink", "Shower", "Bathtub", "Cabinet", 
        "Double Sink", "Washing Machine", "Washing Dryer"
    ]
st.session_state.common_fixtures = common_fixtures

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
            "user_id": st.session_state.user.id,
            "room_name": room_name,
            "calculated_reward": calculated_reward,
            "real_reward": reward
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
        selected_object = st.multiselect( label="Select Objects:", options=objects, key="selected_object")

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

        # delete session state
        st.session_state.available_spaces_dict = None
        st.session_state.positions = None
        st.session_state.bathroom_size = None
        st.session_state.suggestions = None
        st.session_state.selected_fixtures = None
        st.session_state.is_enough_path = None
        st.session_state.space = None
        st.session_state.overall = None
        st.session_state.is_everything = None
        # check if the door is valid
        if selected_door_type == "top":
            y = x
            x = 0
            if y+door_width > room_depth:
                y = room_depth - door_width
        if selected_door_type == "bottom":
            y = x
            x = room_width
            if y+door_width > room_depth:
                y = room_depth - door_width
        if selected_door_type == "right":
            y = room_depth 
            if x+door_width > room_width:
                x = room_width - door_width
        if selected_door_type == "left":
            if x+door_width > room_width:
                x = room_width - door_width
        selected_objects = [objects_map[obj] for obj in selected_object]
   
        windows_doors = [
            ("door1", selected_door_type, x, y, door_width, door_height, 0, selected_door_way),
        ]
        bathroom_size = ( room_width,room_depth)  # Width, Depth, Height

        positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES,attempt=10000)



        
        placed_objects = [pos[5] for pos in positions]
        i = 1
        while len(placed_objects) < len(selected_objects) and i < 3:
            positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES,attempt=10000)
            placed_objects = [pos[5] for pos in positions]
            i += 1
            


        # Find available spaces (returns dict with both sets)
        available_spaces_dict = identify_available_space(positions, (room_width, room_depth), grid_size=1, windows_doors=windows_doors)
        
        # Mark which spaces are accessible and which are inaccessible
        accessible_spaces, inaccessible_spaces = mark_inaccessible_spaces(
            available_spaces_dict['with_shadow'], 
            positions, 
            (room_width, room_depth), 
            windows_doors, 
            grid_size=1,
            min_path_width=30
        )

        # check if there is any space that are not overlap with all other spaces
        for i in range(len(available_spaces_dict['without_shadow'])):
            not_overlapping_spaces = []
            for j in range(len(available_spaces_dict['without_shadow'])):
                if i != j:
                    overlap = check_overlap(available_spaces_dict['without_shadow'][i], available_spaces_dict['without_shadow'][j])
                    if not overlap:
                        not_overlapping_spaces.append(available_spaces_dict['without_shadow'][j])
            if len(not_overlapping_spaces) == len(available_spaces_dict['without_shadow'])-1:
                st.warning(f"Warning: The {available_spaces_dict['without_shadow'][i]} space is not overlapping with all other spaces.")
                
                

        # You can now use these categorized spaces for different purposes
        # For example, warn about inaccessible spaces
        if inaccessible_spaces:
            st.warning(f"Warning: There are {len(inaccessible_spaces)} inaccessible spaces in the room layout.")
            st.write(inaccessible_spaces)
        else:
            st.success("There are no inaccessible spaces in the room layout.")
        # Print the available spaces (both sets)
        print(f"Found {len(available_spaces_dict['with_shadow'])} available spaces (with shadow):")
        for i, space in enumerate(available_spaces_dict['with_shadow']):
            x, y, width, depth = space
            print(f"With Shadow Space {i+1}: Position ({x}, {y}), Size: {width}x{depth} cm")
        print(f"Found {len(available_spaces_dict['without_shadow'])} available spaces (without shadow):")
        for i, space in enumerate(available_spaces_dict['without_shadow']):
            x, y, width, depth = space
            print(f"No Shadow Space {i+1}: Position ({x}, {y}), Size: {width}x{depth} cm")

        # visualization
        fig = visualize_room_with_shadows_3d(bathroom_size, positions, windows_doors)
        isTrue = check_valid_room(positions)
        if isTrue == True:
            st.success("The room is valid.")
        else:
            st.error("The room is invalid.")
        # Show the plot in Streamlit
        st.pyplot(fig)
        fig2 = draw_2d_floorplan(bathroom_size, positions, windows_doors, selected_door_way)
        st.pyplot(fig2)
        #figvis = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces_dict)
        #st.pyplot(figvis)
        st.session_state.positions = positions
        st.session_state.bathroom_size = bathroom_size
        st.session_state.windows_doors = windows_doors
        st.session_state.fig = fig
        st.session_state.fig2 = fig2
        #st.session_state.figvis = figvis
        st.session_state.available_spaces_dict = available_spaces_dict
        
        # Display available spaces visualization
        st.subheader("Available Space Analysis")
        st.write(f"Found {len(available_spaces_dict['with_shadow'])} available spaces (with shadow) and {len(available_spaces_dict['without_shadow'])} available spaces (without shadow)")
        figvis_with_shadow = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces_dict['with_shadow'], shadow = True)
        st.pyplot(figvis_with_shadow)
        st.session_state.figvis_with_shadow = figvis_with_shadow
        figvis_without_shadow = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces_dict['without_shadow'], shadow = False)
        st.pyplot(figvis_without_shadow)
        st.session_state.figvis_without_shadow = figvis_without_shadow

        total_score, detailed_scores = evaluate_room_layout(st.session_state.positions, (room_width, room_depth), OBJECT_TYPES, windows_doors)
        st.write(total_score, detailed_scores)
        # Show space utilization metrics
        if available_spaces_dict['with_shadow'] or available_spaces_dict['without_shadow']:
            total_room_area = room_width * room_depth
            used_area = sum(obj[2] * obj[3] for obj in positions)  # width * depth for each object
            available_area_with_shadow = sum(space[2] * space[3] for space in available_spaces_dict['with_shadow'])
            available_area_without_shadow = sum(space[2] * space[3] for space in available_spaces_dict['without_shadow'])
            
            st.subheader("Space Utilization Metrics")
            col1, col2 = st.columns(2)
            col3, col4 = st.columns(2)
            with col1:
                st.metric("Total Room Area", f"{total_room_area} cm²")
            with col2:
                st.metric("Used Area", f"{used_area} cm² ({int(used_area/total_room_area*100)}%)")
            with col3:
                st.metric("Available Area (with shadow)", f"{available_area_with_shadow} cm² ({int(available_area_with_shadow/total_room_area*100)}%)")
            with col4:
                st.metric("Available Area (without shadow)", f"{available_area_without_shadow} cm² ({int(available_area_without_shadow/total_room_area*100)}%)")
    
    elif st.session_state.fig and st.session_state.fig2:
        st.pyplot(st.session_state.fig)
        st.pyplot(st.session_state.fig2)
        st.pyplot(st.session_state.figvis_with_shadow)
        st.pyplot(st.session_state.figvis_without_shadow)
        st.write(st.session_state.positions)

            



   







    if st.button("Suggest Fixtures"):	
        suggestions = []
        available_spaces_dict = st.session_state.available_spaces_dict
        positions = st.session_state.positions
        bathroom_size = st.session_state.bathroom_size
        #if 'suggestions' not in st.session_state:
        suggestions = suggest_additional_fixtures(positions, bathroom_size, OBJECT_TYPES, available_spaces_dict['with_shadow'], available_spaces_dict['without_shadow'])
        st.session_state.suggestions = suggestions
        fixture_options = list(suggestions["suggestions"].keys())
        st.session_state.fixture_options = fixture_options
        selected_fixtures = fixture_options[:min(2, len(fixture_options))]
        st.session_state.selected_fixtures = selected_fixtures

    # Get suggestions first
    if "suggestions" in st.session_state:
        st.subheader("Suggested Additional Fixtures")
        if st.session_state.suggestions["message"] != "No suitable fixtures can be added to the available spaces":
            # Create a selection for the user
            fixture_options = st.session_state.fixture_options
            selected_fixtures = st.multiselect("Select additional fixtures to add", options=fixture_options, default=st.session_state.selected_fixtures)
            st.session_state.selected_fixtures = selected_fixtures
       
    # Always show the button if there are fixture options
    add_button = st.button("Add Selected Fixtures")
                
    if st.session_state.selected_fixtures and add_button:
        # Add selected fixtures to the layout
        updated_positions, added_objects = add_objects_to_available_spaces(
                positions, 
                (room_width, room_depth), 
                OBJECT_TYPES,
                priority_objects=st.session_state.selected_fixtures,
                available_spaces=st.session_state.available_spaces_dict['with_shadow']
            )

        if added_objects:
            st.success(f"Added {len(added_objects)} new fixtures to the layout!")
            positions = updated_positions + st.session_state.positions
            windows_doors = st.session_state.windows_doors  
                        
            # Update available spaces after adding objects
            available_spaces_dict = identify_available_space(positions, (room_width, room_depth),  windows_doors=windows_doors) #true
            fignew = visualize_room_with_shadows_3d((room_width, room_depth), positions, windows_doors)
            st.pyplot(fignew)
            fignew2 = draw_2d_floorplan((room_width, room_depth), positions, windows_doors, selected_door_way)
            st.pyplot(fignew2)
            fignewvis = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces_dict['with_shadow'], shadow=True)
            st.pyplot(fignewvis)
            fignewvis2 = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces_dict['without_shadow'], shadow=False)
            st.pyplot(fignewvis2)
            st.session_state.new_positions = positions
            st.session_state.fignew = fignew
            st.session_state.fignew2 = fignew2
            st.session_state.fignewvis = fignewvis
            st.session_state.fignewvis2 = fignewvis2
            
            
        else:
            st.warning("Could not add any of the selected fixtures due to space constraints.")
		
		
    is_enough_path = st.checkbox("Is there enough pathway space?")
    is_everything = st.checkbox("Is everything placed?")
    space = st.slider("Space Utilization", 0,10,5)
    overall = st.slider("Overall Satisfaction", 0,10,5)
    st.write("Write your review about the generated room:")
    review = st.text_area("Review", "Write your review here...")
    if st.button("Submit Review"):
        calculated_reward = st.session_state.total_score
        save_data((room_width, room_depth, room_height), st.session_state.positions, st.session_state.windows_doors, review, is_enough_path, space, overall, is_everything, room_name, calculated_reward, reward)
        st.success("Thank you for your review, all data saved to database!")
        


