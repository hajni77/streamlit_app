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
from optimization import identify_available_space, suggest_placement_in_available_space, add_objects_to_available_spaces, suggest_additional_fixtures, switch_objects
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


# -- Setup Supabase connection
supabase: Client = create_client(st.secrets['SUPABASE_URL'], st.secrets['SUPABASE_KEY'])

st.set_page_config(page_title="Floorplan Generator and Visualizer", page_icon=":house:")

try:
    connection = st.connection("supabase", type=SupabaseConnection)
    response = connection.table("reviews").select("*").execute()
    data = response.data
    print("Connection successful!")
except Exception as e:
    print(f"Failed to connect: {e}")

# -- Authentication Section
access_token = auth_section(supabase)
if access_token:
    st.session_state['access_token'] = access_token

# -- Common Fixtures
common_fixtures = [
    "Toilet", "Sink", "Shower", "Bathtub", "Cabinet",
    "Double Sink", "Washing Machine", "Washing Dryer",
]
st.session_state.common_fixtures = common_fixtures

def get_user_supabase():
    token = st.session_state.get('access_token')
    if token:
        return create_client(st.secrets['SUPABASE_URL'], token)
    return supabase

def save_data(room_sizes, positions, doors, review, is_enough_path, space, overall, is_everything, room_name, calculated_reward, reward):
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

        review_data = {
            "room_width": int(room_sizes[0]),
            "room_depth": int(room_sizes[1]),
            "room_height": int(room_sizes[2]),
            "objects": objects,
            "objects_positions": objects_positions,
            "review": {"text": review},
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

        if is_enough_path and space and overall:
            review_data.update({
                "is_enough_path": is_enough_path,
                "space": space,
                "overall": overall,
                "is_everything": is_everything,
            })

        response = supabase.table('reviews').insert(review_data).execute()
        if response.data:
            st.success("Review saved successfully!")
        else:
            st.error("Failed to save review")
    except Exception as e:
        st.error(f"Error saving review: {str(e)}")

# -- Load Object Types
OBJECT_TYPES = []
with open('object_types.json') as f:
    OBJECT_TYPES = json.load(f)

# -- Auth Check
if not st.session_state.auth.get('user'):
    st.warning("Please sign in to access this page")
else:
    # -- Placeholders for Dynamic UI
    title_placeholder = st.empty()
    desc_placeholder = st.empty()
    col1_placeholder = st.empty()
    col2_placeholder = st.empty()
    button_placeholder = st.empty()
    plots_placeholder = st.empty()
    spaces_placeholder = st.empty()

    # -- Fill Static Content
    title_placeholder.title("Floorplan Generator and Visualizer")
    desc_placeholder.write("This app generates a floorplan and visualizes it in 3D.")

    door_images = { 
        "top": "front.png",
        "left": "left.png",
        "right": "right.png",
        "bottom": "back.png",
    }

    objects_map = { 
        "Bathtub": "bathtub",
        "Sink": "sink",
        "Washing Machine": "washing machine",
        "Toilet": "toilet",
        "Shower": "shower",
        "Double Sink": "double sink",
        "Cabinet": "cabinet",
        "Washing Dryer": "washing dryer",
        "Washing Machine and Dryer": "washing machine dryer",
        "Symmetrical Bathtub": "symmetrical bathtub",
        "Asymmetrical Bathtub": "asymmetrical bathtub",
    }

    # -- Room and Object Selection
    with col1_placeholder.container():
        st.subheader("Room Setup")
        room_width = st.number_input("Enter room width:", min_value=50, value=200)
        room_depth = st.number_input("Enter room depth:", min_value=50, value=200)
        room_height = st.number_input("Enter room height:", min_value=100, value=280)

        st.subheader("Select Fixtures")
        objects = list(objects_map.keys())
        selected_object = st.multiselect("Select Objects:", objects)

        rooms = ["Bathroom"]
        selected_room = st.selectbox("Select a Room type:", rooms)

        st.subheader("Door Setup")
        door_types = ["top", "bottom", "right", "left"]
        x = st.number_input("Enter door distance from corner (X):", min_value=1, value=50)
        selected_door_type = st.selectbox("Select door type:", door_types)
        door_width = st.number_input("Enter Door Width:", min_value=1, value=75)
        door_height = st.number_input("Enter Door Height:", min_value=1, value=200)
        selected_door_way = st.selectbox("Door opening direction:", ["Inward", "Outward"])

    with col2_placeholder.container():
        st.subheader("Door Visuals")
        st.image("room.png", caption="Room Image", use_column_width=True)
        door_image = door_images.get(selected_door_type, "default.png")
        st.image(door_image, caption=f"Selected door position: {selected_door_type}", use_column_width=True)

    windows_doors = []
    positions = []
    isTrue = False

    with button_placeholder.container():
        if st.button("Generate 3D Plot"):
            if selected_door_type == "top":
                y = x
                x = 0
                if x + door_width > room_depth:
                    x = room_depth - door_width
            elif selected_door_type == "bottom":
                y = x
                x = room_width
                if x + door_width > room_depth:
                    x = room_depth - door_width
            elif selected_door_type == "right":
                y = room_depth
                if y + door_width > room_width:
                    y = room_width - door_width
            elif selected_door_type == "left":
                if y + door_width > room_width:
                    y = room_width - door_width

            selected_objects = [objects_map[obj] for obj in selected_object]
            windows_doors = [("door1", selected_door_type, x, y, door_width, door_height, 0)]
            bathroom_size = (room_width, room_depth)


            # Calculate total space required for all objects (including shadows)
            room_area = room_width * room_depth
            required_area = 0
            object_areas = []
            
            # Calculate area needed for each object
            for obj_type in filtered_object_list:
                if obj_type in OBJECT_TYPES:
                    obj_def = OBJECT_TYPES[obj_type]
                    optimal_size = obj_def["optimal_size"]
                    #shadow = obj_def["shadow_space"]
                    
                    # Calculate the base area (width * depth)
                    obj_width, obj_depth, _ = optimal_size
                    
                    # # Add shadow to dimensions
                    # shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
                    # total_width = obj_width + shadow_left + shadow_right
                    # total_depth = obj_depth + shadow_top + shadow_bottom
                    
                    # # Calculate total area including shadow
                    # obj_area = total_width * total_depth
                    obj_area = obj_width * obj_depth
                    # Get priority index (higher = more important)
                    # If not in priority list, assign lowest priority
                    priority = priority_list.index(obj_type) if obj_type in priority_list else -1
                    
                    object_areas.append((obj_type, obj_area, priority))
                    required_area += obj_area
            
            # Add 20% for pathways and space between objects
            required_area *= 1.2
            
            print(f"Room area: {room_area} cm², Required area: {required_area:.2f} cm²")
            
            # If room is too small for all objects, return None to indicate error
            if required_area > room_area * 0.9:  # Leave at least 10% for maneuvering
                print(f"ERROR: Room too small for all requested objects. Need {required_area:.2f} cm² but only have {room_area} cm²")
                st.error(f"ERROR: Room too small for all requested objects. Need {required_area:.2f} cm² but only have {room_area} cm²")
            
            positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES, attempt=10000)

            placed_objects = [pos[5] for pos in positions]
            i = 1
            while len(placed_objects) < len(selected_objects) and i < 3:
                positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES, attempt=10000)
                placed_objects = [pos[5] for pos in positions]
                i += 1

            available_spaces_dict = identify_available_space(positions, (room_width, room_depth), grid_size=1, windows_doors=windows_doors)

            fig = visualize_room_with_shadows_3d(bathroom_size, positions, windows_doors)
            isTrue = check_valid_room(positions)

            with plots_placeholder.container():
                if isTrue:
                    st.success("The room is valid.")
                else:
                    st.error("The room is invalid.")

                st.pyplot(fig)
                fig2 = draw_2d_floorplan(bathroom_size, positions, windows_doors, selected_door_way)
                st.pyplot(fig2)

            st.session_state.positions = positions
            st.session_state.bathroom_size = bathroom_size
            st.session_state.windows_doors = windows_doors
            st.session_state.fig = fig
            st.session_state.fig2 = fig2
            st.session_state.available_spaces_dict = available_spaces_dict

            with spaces_placeholder.container():
                st.subheader("Available Space Analysis")
                for idx, space in enumerate(available_spaces_dict['with_shadow']):
                    x, y, width, depth = space
                    st.text(f"With Shadow Space {idx+1}: Position ({x}, {y}), Size {width}x{depth} cm")

                for idx, space in enumerate(available_spaces_dict['without_shadow']):
                    x, y, width, depth = space
                    st.text(f"No Shadow Space {idx+1}: Position ({x}, {y}), Size {width}x{depth} cm")
    # Create placeholders
    suggest_button_placeholder = st.empty()
    suggestions_placeholder = st.empty()
    multiselect_placeholder = st.empty()
    add_button_placeholder = st.empty()
    review_form_placeholder = st.empty()

    # Suggest Fixtures Button
    if suggest_button_placeholder.button("Suggest Fixtures"):
        # Load state
        available_spaces_dict = st.session_state.available_spaces_dict
        positions = st.session_state.positions
        bathroom_size = st.session_state.bathroom_size

        # Get suggestions
        suggestions = suggest_additional_fixtures(
            positions,
            bathroom_size,
            OBJECT_TYPES,
            available_spaces_dict['with_shadow'],
            available_spaces_dict['without_shadow']
        )
        st.session_state.suggestions = suggestions

        # Prepare fixture options
        fixture_options = list(suggestions["suggestions"].keys())
        selected_fixtures = fixture_options[:min(2, len(fixture_options))]
        st.session_state.selected_fixtures = selected_fixtures

    # Show suggestions if available
    if "suggestions" in st.session_state:
        suggestions_placeholder.subheader("Suggested Additional Fixtures")
        suggestions = st.session_state.suggestions
        fixture_options = list(suggestions["suggestions"].keys())
        selected_fixtures = st.session_state.selected_fixtures

        selected_fixtures = multiselect_placeholder.multiselect(
            "Select additional fixtures to add",
            fixture_options,
            default=selected_fixtures
        )
        st.session_state.selected_fixtures = selected_fixtures

    # Add Fixtures Button
    add_button = add_button_placeholder.button("Add Selected Fixtures")

    if st.session_state.selected_fixtures and add_button:
        positions = st.session_state.positions
        available_spaces_dict = st.session_state.available_spaces_dict

        updated_positions, added_objects = add_objects_to_available_spaces(
            positions,
            (room_width, room_depth),
            OBJECT_TYPES,
            priority_objects=st.session_state.selected_fixtures,
            available_spaces=available_spaces_dict['with_shadow']
        )

        if added_objects:
            st.success(f"Added {len(added_objects)} new fixtures to the layout!")
            positions = updated_positions + st.session_state.positions
            windows_doors = st.session_state.windows_doors

            # Update available spaces
            available_spaces_dict = identify_available_space(
                positions, 
                (room_width, room_depth),
                windows_doors=windows_doors
            )

            # Update Visualizations
            fignew = visualize_room_with_shadows_3d((room_width, room_depth), positions, windows_doors)
            st.pyplot(fignew)
            fignew2 = draw_2d_floorplan((room_width, room_depth), positions, windows_doors, selected_door_way)
            st.pyplot(fignew2)
            fignewvis = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces_dict['with_shadow'], shadow=True)
            st.pyplot(fignewvis)
            fignewvis2 = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces_dict['without_shadow'], shadow=False)
            st.pyplot(fignewvis2)

            # Save updated states
            st.session_state.new_positions = positions
            st.session_state.fignew = fignew
            st.session_state.fignew2 = fignew2
            st.session_state.fignewvis = fignewvis
            st.session_state.fignewvis2 = fignewvis2

        else:
            st.warning("Could not add any of the selected fixtures due to space constraints.")

    # Review Form
    with review_form_placeholder.container():
        st.subheader("Feedback")
        is_enough_path = st.checkbox("Is there enough pathway space?")
        is_everything = st.checkbox("Is everything placed?")
        space = st.slider("Space Utilization", 0, 10, 5)
        overall = st.slider("Overall Satisfaction", 0, 10, 5)
        review = st.text_area("Review", "Write your review here...")

        if st.button("Submit Review"):
            save_data(
                (room_width, room_depth, room_height),
                st.session_state.positions,
                st.session_state.windows_doors,
                review,
                is_enough_path,
                space,
                overall,
                is_everything,
                room_name,
                calculated_reward,
                reward
            )
            st.success("Thank you for your review, all data saved to database!")
