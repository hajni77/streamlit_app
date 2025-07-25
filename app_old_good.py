import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import io
import os
import json
import time
import base64
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
from generate_room import fit_objects_in_room
from visualization_file import draw_2d_floorplan, visualize_room_with_shadows_3d, visualize_room_with_available_spaces
from optimization_file import evaluate_room_layout

from layout_ml import LayoutPreferenceModel, get_feature_importance
from layout_rl import LayoutRLModel
from optimization_file import identify_available_space, suggest_placement_in_available_space, add_objects_to_available_spaces, suggest_additional_fixtures, switch_objects, analyze_pathway_accessibility
from visualization_file import visualize_room_with_available_spaces
from utils_file import check_overlap, check_valid_room
from review import render_saved_floorplan, save_data
from optimization_file import evaluate_room_layout, mark_inaccessible_spaces
import psycopg2
from dotenv import load_dotenv
import os
from st_supabase_connection import SupabaseConnection
from supabase import create_client, Client
import time
import io
import base64
from matplotlib import patches
from authentication import auth_section
import json

# Import the new validation system
from models.bathroom import Bathroom
from validation import get_constraint_validator


# Load environment variables from .env
load_dotenv()

# Set up Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configure Streamlit page
st.set_page_config(
    page_title="3D Floorplan Generator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {text-align: center; color: #1E88E5; font-size: 2.5rem; margin-bottom: 1rem;}
    .section-header {color: #0277BD; margin-top: 1rem; margin-bottom: 0.5rem;}
    .success-button {background-color: #4CAF50; color: white; padding: 0.5rem 1rem; border-radius: 5px;}
    .primary-button {background-color: #1E88E5; color: white; padding: 0.5rem 1rem; border-radius: 5px;}
    .warning-button {background-color: #FF9800; color: white; padding: 0.5rem 1rem; border-radius: 5px;}
    .danger-button {background-color: #F44336; color: white; padding: 0.5rem 1rem; border-radius: 5px;}
    .info-box {background-color: #D2F3G4; padding: 1rem; border-radius: 5px; margin: 1rem 0;}
    .metric-card {background-color: #D2F3G4; padding: 1rem; border-radius: 5px; text-align: center;}
    .metric-card-label {font-weight: bold; font-size: 1.7rem; margin: 0.5rem;}
    .metric-card-value {font-size: 2rem; margin: 0.5rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 2rem;}
    .stTabs [data-baseweb="tab"] {height: 4rem;}
    /* Fix for metric alignment */
    .stMetric {vertical-align: top !important;}
    div[data-testid="stMetricLabel"] {justify-content: center !important; text-align: center !important;}
    div[data-testid="stMetricValue"] {justify-content: center !important; text-align: center !important;}
    div[data-testid="stMetricDelta"] {justify-content: center !important; text-align: center !important;}
</style>
""", unsafe_allow_html=True)

# Connect to the database
try:
    connection = st.connection("supabase", type=SupabaseConnection)
    response = connection.table("reviews").select("*").execute()
    data = response.data
    # Store data in session state for use in the Saved Reviews tab
    st.session_state.saved_reviews = data
except Exception as e:
    st.error(f"Failed to connect to database: {e}")
    # Initialize empty list if database connection fails
    if 'saved_reviews' not in st.session_state:
        st.session_state.saved_reviews = []

# Authentication
access_token = auth_section(supabase)
if access_token:
    st.session_state['access_token'] = access_token

# Define objects
common_fixtures = [
    "Toilet", "Sink", "Shower", "Bathtub", "Cabinet", 
    "Double Sink", "Washing Machine", "Washing Dryer",
    "Washing Machine Dryer", "Symmetrical Bathtub", "Asymmetrical Bathtub",
    "Toilet Bidet"
]
st.session_state.common_fixtures = common_fixtures

# Helper: get user-bound supabase client
def get_user_supabase():
    token = st.session_state.get('access_token')
    if token:
        return create_client(st.secrets['SUPABASE_URL'], token)
    return supabase  # fallback to anon/service

# # Function to Save Data to Supabase
# def save_data(room_sizes, positions, doors, review, is_enough_path, space, overall, is_everything, room_name=None, calculated_reward=None, reward=None):
#     if not st.session_state.auth.get('user'):
#         st.error("Please sign in to submit reviews")
#         return False
    
#     with st.spinner("Saving your review to the database..."):
#         try:
#             objects = []
#             objects_positions = []
#             for position in positions:
#                 if isinstance(position, (list, tuple)) and len(position) >= 8:
#                     objects.append({
#                         "name": position[5],
#                         "width": position[2],
#                         "depth": position[3],
#                         "height": position[4]
#                     })
#                     objects_positions.append({
#                         "x": position[0],
#                         "y": position[1],
#                         "must_be_corner": position[6],
#                         "against_wall": position[7]
#                     })

#             # Convert input data to match table schema
#             review_data = {
#                 "room_name": room_name or "My Bathroom Design",
#                 "room_width": int(room_sizes[0]),
#                 "room_depth": int(room_sizes[1]),
#                 "room_height": int(room_sizes[2]),
#                 "objects": objects,
#                 "objects_positions": objects_positions,
#                 "review": {
#                     "text": review,
#                 },
#                 "doors_windows": [{
#                     "type": door[1],
#                     "position": {"x": door[2], "y": door[3]},
#                     "dimensions": {"width": door[4], "height": door[5]}
#                 } for door in doors],
#                 "user_id": st.session_state.user.id,
#                 "room_name": room_name,
#                 "calculated_reward": calculated_reward,
#                 "real_reward": reward
#             }

#             # Add optional fields if available
#             if is_enough_path is not None and space is not None and overall is not None:
#                 review_data.update({
#                     "is_enough_path": is_enough_path,
#                     "space": space,
#                     "overall": overall,
#                     "is_everything": is_everything,
#                 })
                
#             # Insert into Supabase
#             response = supabase.table('reviews').insert(review_data).execute()
#             if response.data:
#                 return True
#             else:
#                 st.error("Failed to save review")
#                 return False
#         except Exception as e:
#             st.error(f"Error saving review: {str(e)}")
#             return False

# Load object types
OBJECT_TYPES = []
with open('object_types.json') as f:
    OBJECT_TYPES = json.load(f)

# Initialize constraint validator for the bathroom
default_validator = get_constraint_validator(room_type="bathroom")

# Define constants for the app
door_images = { 
    "top" : "front.png",
    "left" : "left.png",
    "right" : "right.png",
    "bottom" : "back.png", 
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
    "Washing Machine  Dryer": "washing machine dryer",
    "Symmetrical Bathtub": "symmetrical bathtub",
    "Asymmetrical Bathtub": "asymmetrical bathtub",
    "Toilet Bidet": "toilet bidet"
}

# Check if user is authenticated
if not st.session_state.auth.get('user'):
    st.warning("Please sign in to access this page")
    
else:
    # Main app header
    st.markdown("<h1 class='main-header'>3D Bathroom Floorplan Generator</h1>", unsafe_allow_html=True)
    #st.markdown("<p style='text-align: center; margin-bottom: 2rem;'>Design your perfect bathroom layout with our interactive 3D generator</p>", unsafe_allow_html=True)
    
    # Create tabs for different sections of the app
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📐 Room Setup", "🏠 Visualization", "📊 Analysis", "✍️ Review", "📋 Saved Reviews"])
    
    
    # Initialize session state variables if they don't exist
    if 'generated' not in st.session_state:
        st.session_state.generated = False
    if 'generate_clicked' not in st.session_state:
        st.session_state.generate_clicked = False
    if 'download_clicked' not in st.session_state:
        st.session_state.download_clicked = False
    if 'review_submitted' not in st.session_state:
        st.session_state.review_submitted = False
    
    # Initialize ML model if not already in session state
    # Initialize ML model if not already in session state
    if 'ml_model' not in st.session_state:
        st.session_state.ml_model = LayoutPreferenceModel()
        
        # Try to load the model from local storage first
        local_load_success = st.session_state.ml_model.load_model()
        
        # If we're on Streamlit Cloud and have Supabase set up, also try loading from there
        try:
            # Only attempt Supabase if we have the client properly initialized
            if 'supabase' in locals() or 'supabase' in globals():
                supabase_loaded = st.session_state.ml_model.load_model_from_supabase(supabase)
                if supabase_loaded:
                    print("ML Model loaded from Supabase storage")
        except Exception as e:
            print(f"Note: Could not load ML model from Supabase: {e}")
    
    # Initialize RL model if not already in session state
    if 'rl_model' not in st.session_state:
        st.session_state.rl_model = LayoutRLModel()
        
        # Try to load the model from local storage first
        local_load_success = st.session_state.rl_model.load_model()
        
        # If we're on Streamlit Cloud and have Supabase set up, also try loading from there
        try:
            # Only attempt Supabase if we have the client properly initialized
            if 'supabase' in locals() or 'supabase' in globals():
                supabase_loaded = st.session_state.rl_model.load_model_from_supabase(supabase)
                if supabase_loaded:
                    print("RL Model loaded from Supabase storage")
        except Exception as e:
            print(f"Note: Could not load RL model from Supabase: {e}")
            
        st.session_state.ml_update_needed = False
        st.session_state.rl_update_needed = False
        
    # Track if we need to update the models with a new selection
    if 'ml_update_needed' not in st.session_state:
        st.session_state.ml_update_needed = False
    if 'rl_update_needed' not in st.session_state:
        st.session_state.rl_update_needed = False
        
    # Save models if they have been updated
    # Save ML model if updated
    if st.session_state.ml_update_needed:
        # Always save to local storage
        st.session_state.ml_model.save_model()
        
        # Try to save to Supabase if available
        try:
            # Only attempt Supabase if we have the client properly initialized
            if 'supabase' in locals() or 'supabase' in globals():
                st.session_state.ml_model.save_model_to_supabase(supabase)
                print("Model also saved to Supabase storage")
        except Exception as e:
            print(f"Note: Could not save to Supabase: {e}")
            
        # Reset the update flag
        st.session_state.ml_update_needed = False
    
    # Save RL model if updated
    if st.session_state.rl_update_needed:
        # Always save to local storage
        st.session_state.rl_model.save_model()
        
        # Try to save to Supabase if available
        try:
            if st.session_state.auth.get('user'):
                user_id = st.session_state.auth.get('user').get('id')
                st.session_state.rl_model.save_model_to_supabase(supabase, user_id)
                print("RL Model saved to Supabase storage")
        except Exception as e:
            print(f"Could not save RL model to Supabase: {e}")
            
        # Reset the update flag
        st.session_state.rl_update_needed = False
    
    if 'room_width' not in st.session_state:
        st.session_state.room_width = 200
    if 'room_depth' not in st.session_state:
        st.session_state.room_depth = 200
    if 'room_height' not in st.session_state:
        st.session_state.room_height = 280
    if 'saved_reviews' not in st.session_state:
        st.session_state.saved_reviews = []

    # Room Setup Tab Content
    with tab1:
        st.markdown("<h2 class='section-header'>Room Dimensions & Objects</h2>", unsafe_allow_html=True)
        
        # Create two columns for the entire room setup - left for inputs, right for images
        left_col, right_col = st.columns([1, 1])
        
        with left_col:
            # Room dimensions section
            st.markdown("<h3 class='section-header'>Room Dimensions</h3>", unsafe_allow_html=True)
            
            # Create 3 columns for room dimensions
            dim_col1, dim_col2, dim_col3 = st.columns(3)
            
            with dim_col1:
                room_width = st.number_input(
                    "Room Width (cm)", 
                    min_value=50, 
                    max_value=1000,
                    value=st.session_state.room_width,
                    step=10,
                    help="Width of the room in centimeters"
                )
                st.session_state.room_width = room_width
                
            with dim_col2:
                room_depth = st.number_input(
                    "Room Depth (cm)", 
                    min_value=50, 
                    max_value=1000,
                    value=st.session_state.room_depth,
                    step=10,
                    help="Depth of the room in centimeters"
                )
                st.session_state.room_depth = room_depth
                
            with dim_col3:
                room_height = st.number_input(
                    "Room Height (cm)", 
                    min_value=100, 
                    max_value=400,
                    value=st.session_state.room_height,
                    step=10,
                    help="Height of the room in centimeters"
                )
                st.session_state.room_height = room_height
            
            # Divider
            st.markdown("<hr style='margin: 1rem 0'>", unsafe_allow_html=True)
            
            # Fixture selection section
            st.markdown("<h3 class='section-header'>Select Objects</h3>", unsafe_allow_html=True)
            st.markdown("<p>Choose the objects you want to include in your bathroom design:</p>", unsafe_allow_html=True)
            
            # Create a more visual fixture selection with 3 columns, FROM OBJECTS MAP
            objects = list(objects_map.keys())
            
            # Create a 3-column layout for fixture selection
            fixture_cols = st.columns(3)
            
            # Distribute fixtures across columns
            selected_object = []
            for i, fixture in enumerate(objects):
                with fixture_cols[i % 3]:
                    if st.checkbox(fixture, key=f"fixture_{fixture}"):
                        selected_object.append(fixture)
            
            # Display selected fixtures summary
            if selected_object:
                st.markdown(f"<div class='info-box'>Selected objects: {', '.join(selected_object)}</div>", unsafe_allow_html=True)
            else:
                st.warning("Please select at least one object for your bathroom")
            
            # Divider
            st.markdown("<hr style='margin: 1rem 0'>", unsafe_allow_html=True)
            
            # Door configuration section
            st.markdown("<h3 class='section-header'>Door Configuration</h3>", unsafe_allow_html=True)
            
            # Create 3 columns for door dimensions (similar to room dimensions)
            door_dim_col1, door_dim_col2, door_dim_col3 = st.columns(3)
            
            with door_dim_col1:
                # Door position selection
                door_type = ["top", "bottom", "right", "left"]
                selected_door_type = st.selectbox(
                    "Door Wall Position:", 
                    door_type,
                    help="Select which wall the door is positioned on"
                )
            
            with door_dim_col2:
                # Door dimensions
                door_width = st.number_input(
                    "Door Width (cm)", 
                    min_value=60, 
                    max_value=120,
                    value=75,
                    step=5,
                    help="Width of the door in centimeters"
                )
            
            with door_dim_col3:
                door_height = st.number_input(
                    "Door Height (cm)", 
                    min_value=180, 
                    max_value=240,
                    value=200,
                    step=5,
                    help="Height of the door in centimeters"
                )
            
            # Door distance from corner
            x = st.slider(
                "Distance from Corner (cm):", 
                min_value=1, 
                max_value=min(room_width, room_depth) - 50,
                value=50,
                help="Distance from the corner of the room"
            )
            
            # Door swing direction
            door_options = ["Inward", "Outward"]
            selected_door_way = st.radio(
                "Door Swing Direction:", 
                door_options,
                help="Direction the door opens"
            )
            
            # Door hinge side
            door_hinge_options = ["Left", "Right"]
            selected_door_hinge = st.radio(
                "Door Hinge Side:", 
                door_hinge_options,
                help="Side where the door hinges are located (left or right)"
            )
        
        with right_col:
            # Room and door visualization
            st.markdown("<h3 class='section-header'>Room Preview</h3>", unsafe_allow_html=True)
            
            im_col1, im_col2 = st.columns([1, 1])
            with im_col1:
                # Create and display room dimension visualization
                fig, ax = plt.subplots(figsize=(5, 5))
                # Draw rectangle with room dimensions
                room_rect = plt.Rectangle((0, 0), room_depth, room_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                ax.add_patch(room_rect)
                
                # Set plot limits with some padding
                padding = max(room_depth, room_width) * 0.1
                ax.set_xlim(-padding, room_depth + padding)
                ax.set_ylim(-padding, room_width + padding)
                
                # Add dimension labels
                ax.text(room_depth/2, -padding/2, f'{room_depth:.1f}cm', ha='center', va='top')
                ax.text(-padding/2, room_width/2, f'{room_width:.1f}cm', ha='right', va='center', rotation=90)
                
                # Add center point
                ax.plot(room_depth/2, room_width/2, 'ro')

                # add door based on selected door type, way, and hinge side
                if selected_door_type == "top":
                    if selected_door_way == "Inward":
                        door_rect = plt.Rectangle((x, room_width - door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                        # Add hinge indicator
                        if selected_door_hinge == "Right":
                            # Left hinge (from outside perspective)
                            ax.plot([x, x], [room_width, room_width - door_width], 'k-', linewidth=3)
                            # Door swing arc
                            arc = patches.Arc((x, room_width ), door_width*2, door_width*2, 
                                            angle=-90, theta1=0, theta2=90, linewidth=1, color='gray', linestyle='--')
                            ax.add_patch(arc)
                        else: # Right hinge
                            # Right hinge (from outside perspective)
                            ax.plot([x + door_width, x + door_width], [room_width, room_width - door_width], 'k-', linewidth=3)
                            # Door swing arc
                            arc = patches.Arc((x + door_width, room_width ), door_width*2, door_width*2, 
                                            angle=90, theta1=90, theta2=180, linewidth=1, color='gray', linestyle='--')
                            ax.add_patch(arc)
                    elif selected_door_way == "Outward":
                        door_rect = plt.Rectangle((x, room_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                        # Add hinge indicator
                        if selected_door_hinge == "Left":
                            # Left hinge (from outside perspective)
                            ax.plot([x, x], [room_width, room_width + door_width], 'k-', linewidth=3)
                            # Door swing arc
                            # arc = patches.Arc((x, room_width), door_width*2, door_width*2, 
                            #                 angle=0, theta1=270, theta2=360, linewidth=1, color='gray', linestyle='--')
                            # ax.add_patch(arc)
                        else: # Right hinge
                            # Right hinge (from outside perspective)
                            ax.plot([x + door_width, x + door_width], [room_width, room_width + door_width], 'k-', linewidth=3)
                            # Door swing arc
                            # arc = patches.Arc((x + door_width, room_width), door_width*2, door_width*2, 
                            #                 angle=0, theta1=180, theta2=270, linewidth=1, color='gray', linestyle='--')
                            # ax.add_patch(arc)
                    ax.text(x+door_width/2, room_width, f'{door_width:.1f}cm', ha='center', va='bottom')
                    # distance from corner
                    ax.text(x/2,room_width, f'{x:.1f}cm', ha='center', va='bottom')
                    ax.text(x+door_width + x/2, room_width, f'{room_depth-door_width-x:.1f}cm', ha='center', va='bottom')
                elif selected_door_type == "bottom":
                    if selected_door_way == "Inward":
                        door_rect = plt.Rectangle((x, 0), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                        # Add hinge indicator
                        if selected_door_hinge == "Left":
                            # Left hinge (from outside perspective)
                            ax.plot([x, x], [0, door_width], 'k-', linewidth=3)
                            # Door swing arc
                            arc = patches.Arc((x, 0), door_width*2, door_width*2, 
                                            angle=0, theta1=0, theta2=90, linewidth=1, color='gray', linestyle='--')
                            ax.add_patch(arc)
                        else: # Right hinge
                            # Right hinge (from outside perspective)
                            ax.plot([x + door_width, x + door_width], [0, door_width], 'k-', linewidth=3)
                            # Door swing arc
                            arc = patches.Arc((x + door_width, 0), door_width*2, door_width*2, 
                                            angle=0, theta1=90, theta2=180, linewidth=1, color='gray', linestyle='--')
                            ax.add_patch(arc)
                    elif selected_door_way == "Outward":
                        door_rect = plt.Rectangle((x, -door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                        # Add hinge indicator
                        if selected_door_hinge == "Left":
                            # Left hinge (from outside perspective)
                            ax.plot([x, x], [0, -door_width], 'k-', linewidth=3)
                            # Door swing arc
                            # arc = patches.Arc((x, 0), door_width*2, door_width*2, 
                            #                 angle=0, theta1=0, theta2=90, linewidth=1, color='gray', linestyle='--')
                            # ax.add_patch(arc)
                        else: # Right hinge
                            # Right hinge (from outside perspective)
                            ax.plot([x + door_width, x + door_width], [0, -door_width], 'k-', linewidth=3)
                            # Door swing arc
                            # arc = patches.Arc((x + door_width, 0), door_width*2, door_width*2, 
                            #                 angle=0, theta1=270, theta2=360, linewidth=1, color='gray', linestyle='--')
                            # ax.add_patch(arc)
                    # distance from corner
                    ax.text(x/2, 0, f'{x:.1f}cm', ha='center', va='bottom')
                    ax.text(x+door_width/2,0, f'{door_width:.1f}cm', ha='center', va='bottom')
                    ax.text(x+door_width + x/2, 0, f'{room_depth-door_width-x:.1f}cm', ha='center', va='bottom')
                elif selected_door_type == "right":
                    if selected_door_way == "Inward":
                        door_rect = plt.Rectangle((room_depth - door_width, room_width-x-door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                        # Add hinge indicator
                        if selected_door_hinge == "Left":
                            # Left hinge from outside perspective (top of the door in this orientation)
                            ax.plot([room_depth - door_width, room_depth], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                            # Door swing arc
                            arc = patches.Arc((room_depth, room_width-x-door_width), door_width*2, door_width*2, 
                                            angle=270, theta1=180, theta2=270, linewidth=1, color='gray', linestyle='--')
                            ax.add_patch(arc)
                        else: # Right hinge
                            # Right hinge from outside perspective (bottom of the door in this orientation)
                            ax.plot([room_depth - door_width, room_depth], [room_width-x, room_width-x], 'k-', linewidth=3)
                            # Door swing arc
                            arc = patches.Arc((room_depth , room_width-x), door_width*2, door_width*2, 
                                            angle=270, theta1=270, theta2=360, linewidth=1, color='gray', linestyle='--')
                            ax.add_patch(arc)
                    elif selected_door_way == "Outward":
                        door_rect = plt.Rectangle((room_depth, room_width-x-door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                        # Add hinge indicator
                        if selected_door_hinge == "Left":
                            # Left hinge from outside perspective (top of the door in this orientation)
                            ax.plot([room_depth, room_depth + door_width], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                            # Door swing arc
                            # arc = patches.Arc((room_depth, room_width-x-door_width), door_width*2, door_width*2, 
                            #                 angle=270, theta1=180, theta2=270, linewidth=1, color='gray', linestyle='--')
                            # ax.add_patch(arc)
                        else: # Right hinge
                            # Right hinge from outside perspective (bottom of the door in this orientation)
                            ax.plot([room_depth, room_depth + door_width], [room_width-x, room_width-x], 'k-', linewidth=3)
                            # Door swing arc
                            # arc = patches.Arc((room_depth, room_width-x), door_width*2, door_width*2, 
                            #                 angle=270, theta1=90, theta2=180, linewidth=1, color='gray', linestyle='--')
                            # ax.add_patch(arc)
                    ax.text(room_depth + padding/2, room_width-x-door_width/2, f'{door_width:.1f}cm', ha='right', va='center', rotation=90)
                    ax.text(room_depth + padding/2, padding, f'{room_width-door_width-x:.1f}cm', ha='right', va='center', rotation=90)
                    ax.text(room_depth + padding/2, room_width-x/2, f'{x:.1f}cm', ha='right', va='center', rotation=90)
                elif selected_door_type == "left":
                    if selected_door_way == "Inward":
                        door_rect = plt.Rectangle((0, room_width-x-door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                        # Add hinge indicator
                        if selected_door_hinge == "Left":
                            # Left hinge from outside perspective (bottom of the door in this orientation)
                            ax.plot([0, door_width], [room_width-x, room_width-x], 'k-', linewidth=3)
                            # Door swing arc
                            arc = patches.Arc((0, room_width-x), door_width*2, door_width*2, 
                                            angle=90, theta1=180, theta2=270, linewidth=1, color='gray', linestyle='--')
                            ax.add_patch(arc)
                        else: # Right hinge
                            # Right hinge from outside perspective (top of the door in this orientation)
                            ax.plot([0, door_width], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                            # Door swing arc
                            arc = patches.Arc((0, room_width-x-door_width), door_width*2, door_width*2, 
                                            angle=90, theta1=270, theta2=360, linewidth=1, color='gray', linestyle='--')
                            ax.add_patch(arc)
                    elif selected_door_way == "Outward":
                        door_rect = plt.Rectangle((-door_width, room_width-x-door_width), door_width, door_width, linewidth=2, edgecolor='#1f77b4', facecolor='#e6f3ff')
                        # Add hinge indicator
                        if selected_door_hinge == "Left":
                            # Left hinge from outside perspective (bottom of the door in this orientation)
                            ax.plot([0, -door_width], [room_width-x, room_width-x], 'k-', linewidth=3)
                            # Door swing arc
                            # arc = patches.Arc((0, room_width-x), door_width*2, door_width*2, 
                            #                 angle=90, theta1=0, theta2=90, linewidth=1, color='gray', linestyle='--')
                            # ax.add_patch(arc)
                        else: # Right hinge
                            # Right hinge from outside perspective (top of the door in this orientation)
                            ax.plot([0, -door_width], [room_width-x-door_width, room_width-x-door_width], 'k-', linewidth=3)
                            # Door swing arc
                            # arc = patches.Arc((0, room_width-x-door_width), door_width*2, door_width*2, 
                            #                 angle=90, theta1=270, theta2=360, linewidth=1, color='gray', linestyle='--')
                            # ax.add_patch(arc)
                    ax.text(0+ padding/2, room_width-x-door_width/2, f'{door_width:.1f}cm', ha='right', va='center', rotation=90)
                    ax.text(0+padding/2, padding, f'{room_width-door_width-x:.1f}cm', ha='right', va='center', rotation=90)
                    ax.text(0+padding/2, room_width-x/2, f'{x:.1f}cm', ha='right', va='center', rotation=90)
                #ax.add_patch(door_rect)
                
                # Remove axis ticks and labels for cleaner look
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_aspect('equal')
                plt.tight_layout()
                
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
            
            #with im_col2:
                # Display door position image based on selection
                #door_image = door_images.get(selected_door_type, "default.png")
                #st.image(door_image, caption=f"Selected door position: {selected_door_type}", use_column_width=True)

                # draw rectangle with r
        
        # Initialize y value based on door position
        y = 0
        
        # Generate button
        st.markdown("<hr style='margin: 1.5rem 0'>", unsafe_allow_html=True)
        generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
        
        with generate_col2:
            generate_button = st.button(
                "Generate 3D Floorplan", 
                use_container_width=True,
                type="primary",
                help="Click to generate the 3D floorplan with your selected options"
            )
            if generate_button :
                if (len(selected_object)==0 ):
                    st.error("Please select at least one object to generate the 3D floorplan")
                else:
                    st.session_state.generate_clicked = True
                    st.session_state.selected_layout_index = None

    windows_doors = []
    isTrue = False
    positions = []
    
    # Generate Floorplan Logic
    # Check if this is a new generation request or if we're coming from a review submission
    if 'review_submitted' in st.session_state and st.session_state.review_submitted:
        # If we just submitted a review, don't regenerate
        st.session_state.review_submitted = False
    # check if this is a new generation request or if we're coming from a download button
    elif 'download_clicked' in st.session_state and st.session_state.download_clicked and not st.session_state.generate_clicked:
        st.session_state.download_clicked = False
    elif generate_button or ('generate_clicked' in st.session_state and st.session_state.generate_clicked and not st.session_state.download_clicked):
        st.session_state.generate_clicked = False
        
        # Switch to the Visualization tab
        st.query_params = 'visualization'
        # Calculate total space required for all objects (including shadows)
        room_area = room_width * room_depth
        required_area = 0
        object_areas = []
        
        # Calculate area needed for each object
        for obj_type in selected_object:
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

        
        # Show a progress bar during generation
        with st.spinner("Generating your 3D floorplan..."):
            # Clear previous session state
            st.session_state.available_spaces_dict = None
            st.session_state.positions = None
            st.session_state.bathroom_size = None
            st.session_state.suggestions = None
            st.session_state.selected_fixtures = None
            st.session_state.is_enough_path = None
            st.session_state.space = None
            st.session_state.overall = None
            st.session_state.is_everything = None
            
            # Adjust door position based on selected type
            if selected_door_type == "top":
                y = x
                x = 0
                if y+door_width > room_depth:
                    y = room_depth - door_width
            elif selected_door_type == "bottom":
                y = x
                x = room_width
                if y+door_width > room_depth:
                    y = room_depth - door_width
            elif selected_door_type == "right":
                y = room_depth 
                if x+door_width > room_width:
                    x = room_width - door_width
            elif selected_door_type == "left":
                if x+door_width > room_width:
                    x = room_width - door_width
                    
            # Map selected objects to internal names
            selected_objects = [objects_map[obj] for obj in selected_object]
            
            # Define door parameters
            windows_doors = [
                ("door1", selected_door_type, x, y, door_width, door_height, 0, selected_door_way, selected_door_hinge),
            ]
            
            # Set bathroom dimensions
            bathroom_size = (room_width, room_depth)
            
            # Generate multiple room layouts and select the best one
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            # Number of layouts to generate
            num_layouts = 10
            
            # Store all generated layouts
            all_layouts = []
            layout_scores = []
            
            progress_text.text(f"Generating {num_layouts} different room layouts...")
            
            # Generate multiple layouts
            for i in range(num_layouts):
                progress_text.text(f"Generating layout {i+1}/{num_layouts}...")
                progress_bar.progress((i / num_layouts) *0.6 )  # Use 60% of progress bar for generation
                
                # Generate a layout
                layout_positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES, attempt=10000)
                if layout_positions is None:
                    st.error("Room too small for all objects.")
                    break
                # Extract just the placed objects
                layout_objects = [pos for pos in layout_positions if pos[5].lower() in [obj_name.lower() for obj_name in selected_objects]]
                # Store the layout if it contains at least some objects
                if layout_objects:
                    all_layouts.append(layout_objects)
            
            # If we have layouts, show all of them for user selection
            if all_layouts:
                progress_text.text("Evaluating all layouts...")
                progress_bar.progress(0.7)  # 70% progress
                
                # Use the compare_room_layouts function to evaluate all layouts
                from optimization_file import compare_room_layouts
                best_layout, best_score, all_scores = compare_room_layouts(
                    all_layouts, 
                    bathroom_size, 
                    OBJECT_TYPES, 
                    windows_doors=windows_doors,
                    requested_objects=selected_objects
                )
                


                
                # Use the best layout
                # progress_text.text(f"Selected best layout with score: {best_score:.2f}/100")
                # progress_bar.progress(0.9)  # 90% progress
                # positions = best_layout
                # placed_objects = [pos[5] for pos in positions]
                
                # Store all scores and best layout in session state
                # Store enriched scores data format: [(layout, score, detailed_scores), ...]
                st.session_state.layout_scores = all_scores
                st.session_state.all_layouts = all_layouts
                st.session_state.all_scores = all_scores
                #st.session_state.best_layout_score = best_score
                #st.session_state.total_score = best_score  # Update the main score variable
                
                # Extract layout performance metrics
                room_width, room_depth = bathroom_size
                layout_metrics = []
                
                for i, (layout, score, detailed_scores) in enumerate(all_scores):
                    # Calculate object placement percentage
                    placed_objects_count = len(layout)
                    placement_percentage = (placed_objects_count / len(selected_objects)) * 100 if selected_objects else 100
                    
                    # Calculate space efficiency
                    total_area = room_width * room_depth
                    used_area = sum(obj[2] * obj[3] for obj in layout)  # width * depth
                    space_efficiency = (used_area / total_area) * 100
                    
                    # Store metrics
                    layout_metrics.append({
                        "layout_id": i + 1,  # 1-based indexing for display
                        "score": score,
                        "placed_percentage": placement_percentage,
                        "space_efficiency": space_efficiency,
                        "detailed_scores": detailed_scores
                    })
                
                st.session_state.layout_metrics = layout_metrics
                
                # Use ML model to predict the best layout if available
                if st.session_state.ml_model.model is not None:
                    try:
                        # The ML model expects all_scores in the format [(layout, score, detailed_scores), ...]
                        ml_best_idx = st.session_state.ml_model.predict_best_layout(all_layouts, all_scores, layout_metrics)
                        # Store the ML recommendation
                        st.session_state.ml_recommended_layout = ml_best_idx
                    except Exception as e:
                        st.warning(f"ML model prediction failed: {e}")
                        st.session_state.ml_recommended_layout = None
                
                # Use RL model to predict the best layout if available
                if hasattr(st.session_state, 'rl_model') and st.session_state.rl_model is not None:
                    try:
                        # Extract the required data from all_scores
                        # all_scores format: [(layout, score, detailed_scores), ...]
                        layouts = [item[0] for item in all_scores]
                        scores = [item[1] for item in all_scores]
                        detailed_scores = [item[2] for item in all_scores]
                        
                        rl_best_idx = st.session_state.rl_model.predict_best_layout(layouts, scores, detailed_scores, layout_metrics)
                        # Store the RL recommendation
                        st.session_state.rl_recommended_layout = rl_best_idx
                    except Exception as e:
                        st.warning(f"RL model prediction failed: {e}")
                        st.session_state.rl_recommended_layout = None
                
                # Display all layouts as 2D floorplans for selection
                progress_text.text("Select your preferred layout:")
                progress_bar.progress(0.9)  # 90% progress
                
                # Create a container for the layout selection
                layout_selection_container = st.container()
                
                # with layout_selection_container:
                #     st.markdown("<h3 class='section-header'>Select Your Preferred Layout</h3>", unsafe_allow_html=True)
                    
                #     # Create columns for layout selection
                #     layout_cols = st.columns(min(3, len(all_layouts)))
                #     selected_layout_index = None
                    
                #     # Display each layout as a 2D floorplan with selection button
                #     for i, (layout, score, detailed_scores) in enumerate(all_scores):
                #         col_index = i % len(layout_cols)
                #         with layout_cols[col_index]:
                #             # Create 2D floorplan
                #             fig = draw_2d_floorplan(bathroom_size, layout, windows_doors, indoor=True)
                #             st.pyplot(fig)
                            
                #             # Display score and metrics
                #             st.markdown(f"**Layout {i+1}**")
                #             st.markdown(f"Score: {score:.1f}/100")
                #             st.markdown(f"Objects Placed: {layout_metrics[i]['placed_percentage']:.1f}%")
                            
                #             # Selection button
                #             if st.button(f"Select Layout {i+1}", key=f"select_layout_ok{i}"):
                #                 selected_layout_index = i
                    
                #     # If a layout is selected, use it
                #     if selected_layout_index is not None:
                #         positions = all_scores[selected_layout_index][0]
                #         placed_objects = [pos[5] for pos in positions]
                #         best_score = all_scores[selected_layout_index][1]
                #         detailed_scores = all_scores[selected_layout_index][2]
                        
                #         st.session_state.best_layout_score = best_score
                #         st.session_state.total_score = best_score  # Update the main score variable
                #         st.session_state.detailed_scores = detailed_scores
                        
                #         st.success(f"You selected Layout {selected_layout_index + 1} with score: {best_score:.1f}/100")
                #     else:
                #         # Default to the highest-scoring layout if none selected
                #         best_layout_index = max(range(len(all_scores)), key=lambda i: all_scores[i][1])
                #         positions = all_scores[best_layout_index][0]
                #         placed_objects = [pos[5] for pos in positions]
                #         best_score = all_scores[best_layout_index][1]
                #         detailed_scores = all_scores[best_layout_index][2]
                        
                #         st.session_state.best_layout_score = best_score
                #         st.session_state.total_score = best_score  # Update the main score variable
                #         st.session_state.detailed_scores = detailed_scores
            else:
                # Fallback if no good layouts were found
                progress_text.text("Optimizing object placement...")
                progress_bar.progress(0.7) 

                
                # Traditional approach as fallback
                positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES, attempt=10000)
                placed_objects = [pos[5] for pos in positions]
                retry_count = 1
                
                while len(placed_objects) < len(selected_objects) and retry_count < 3  :
                    positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES, attempt=10000)
                    placed_objects = [pos[5] for pos in positions]
                    retry_count += 1
            
            # Find available spaces
            progress_text.text("Analyzing available spaces...")
            available_spaces_dict = identify_available_space(positions, (room_width, room_depth), grid_size=1, windows_doors=windows_doors)
            
            # Mark accessible and inaccessible spaces
            progress_text.text("Evaluating accessibility...")
            accessible_spaces, inaccessible_spaces = mark_inaccessible_spaces(
                available_spaces_dict['with_shadow'], 
                positions, 
                (room_width, room_depth), 
                windows_doors, 
                grid_size=1,
                min_path_width=30
            )
            
            # Check for non-overlapping spaces
            non_overlapping_spaces = []
            for i in range(len(available_spaces_dict['without_shadow'])):
                not_overlapping_spaces = []
                for j in range(len(available_spaces_dict['without_shadow'])):
                    if i != j:
                        overlap = check_overlap(available_spaces_dict['without_shadow'][i], available_spaces_dict['without_shadow'][j])
                        if not overlap:
                            not_overlapping_spaces.append(available_spaces_dict['without_shadow'][j])
                if len(not_overlapping_spaces) == len(available_spaces_dict['without_shadow'])-1:
                    non_overlapping_spaces.append(available_spaces_dict['without_shadow'][i])
            
            # Store results in session state
            st.session_state.positions = positions
            st.session_state.bathroom_size = bathroom_size
            st.session_state.windows_doors = windows_doors
            st.session_state.available_spaces_dict = available_spaces_dict
            st.session_state.accessible_spaces = accessible_spaces
            st.session_state.inaccessible_spaces = inaccessible_spaces
            st.session_state.non_overlapping_spaces = non_overlapping_spaces
            st.session_state.generated = True
            
            # Calculate layout score
            progress_text.text("Evaluating layout quality...")
            total_score, detailed_scores = evaluate_room_layout(positions, (room_width, room_depth), OBJECT_TYPES, windows_doors, selected_object)
            print("total score", total_score)
            st.session_state.total_score = total_score
            st.session_state.detailed_scores = detailed_scores

            # Create visualizations
            progress_text.text("Creating visualizations...")
            
            # Create 3D visualization
            fig = visualize_room_with_shadows_3d(bathroom_size, positions, windows_doors)
            st.session_state.fig = fig
            
# Save 3D figure to bytes for download
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            st.session_state.fig_bytes = buf.getvalue()
            
            # Create 2D floorplan
            fig2 = draw_2d_floorplan(bathroom_size, positions, windows_doors, selected_door_way)
            st.session_state.fig2 = fig2
            
            # Save 2D figure to bytes for download
            buf2 = io.BytesIO()
            fig2.savefig(buf2, format='png', dpi=300, bbox_inches='tight')
            buf2.seek(0)
            st.session_state.fig2_bytes = buf2.getvalue()
            
            progress_text.text("Visualizing available spaces...")
            progress_bar.progress(0.99)  # Use 60% of progress bar for generation
            figvis_with_shadow = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces_dict['with_shadow'], shadow=True)
            st.session_state.figvis_with_shadow = figvis_with_shadow
            
            # Save figure to bytes for download
            buf3 = io.BytesIO()
            figvis_with_shadow.savefig(buf3, format='png', dpi=300, bbox_inches='tight')
            buf3.seek(0)
            st.session_state.figvis_with_shadow_bytes = buf3.getvalue()
            
            figvis_without_shadow = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces_dict['without_shadow'], shadow=False)
            st.session_state.figvis_without_shadow = figvis_without_shadow
            
            #Save figure to bytes for download
            buf4 = io.BytesIO()
            figvis_without_shadow.savefig(buf4, format='png', dpi=300, bbox_inches='tight')
            buf4.seek(0)
            st.session_state.figvis_without_shadow_bytes = buf4.getvalue()
            
            # Calculate space utilization metrics
            total_room_area = room_width * room_depth
            used_area = sum(obj[2] * obj[3] for obj in positions)  # width * depth for each object
            available_area_with_shadow = sum(space[2] * space[3] for space in available_spaces_dict['with_shadow'])
            available_area_without_shadow = sum(space[2] * space[3] for space in available_spaces_dict['without_shadow'])
            
            st.session_state.space_metrics = {
                "total_room_area": total_room_area,
                "used_area": used_area,
                "available_area_with_shadow": available_area_with_shadow,
                "available_area_without_shadow": available_area_without_shadow
            }
            
            # Check if room is valid
            isTrue = check_valid_room(positions)
            st.session_state.is_valid_room = isTrue
    
    # Visualization Tab Content
    with tab2:
        if not st.session_state.get('generated', False):
            st.info("Please generate a floorplan first in the Room Setup tab")
        else:
            st.markdown("<h2 class='section-header'>Bathroom Layout Selection & Visualization</h2>", unsafe_allow_html=True)
            
            # # Room validity indicator
            # if st.session_state.is_valid_room:
            #     st.success("✅ The room layout is valid and meets all constraints")
            # else:
            #     st.error("❌ The room layout is invalid - some constraints are not satisfied")
            
            # Track the selected layout index if not already set
            if 'selected_layout_index' not in st.session_state:
                st.session_state.selected_layout_index = None
                
            # Check if we have multiple layouts to display and no layout has been selected yet
            if hasattr(st.session_state, 'layout_scores') and st.session_state.layout_scores and st.session_state.selected_layout_index is None:
                # Display all layouts as 2D floorplans for selection
                st.markdown("<h3 class='section-header'>Select Your Preferred Layout </h3>", unsafe_allow_html=True)
                # Display recommendations from both models if available
                if hasattr(st.session_state, 'ml_recommended_layout') and st.session_state.ml_recommended_layout is not None:
                    ml_recommended_layout = st.session_state.ml_recommended_layout + 1
                    st.markdown(f"<p>ML Model Recommended Layout: {ml_recommended_layout}</p>", unsafe_allow_html=True)
                
                if hasattr(st.session_state, 'rl_recommended_layout') and st.session_state.rl_recommended_layout is not None:
                    rl_recommended_layout = st.session_state.rl_recommended_layout + 1
                    st.markdown(f"<p>RL Model Recommended Layout: {rl_recommended_layout}</p>", unsafe_allow_html=True)
                    
                # If both models agree on a recommendation, highlight it
                if (hasattr(st.session_state, 'ml_recommended_layout') and 
                    hasattr(st.session_state, 'rl_recommended_layout') and 
                    st.session_state.ml_recommended_layout == st.session_state.rl_recommended_layout):
                    agreed_layout = st.session_state.ml_recommended_layout + 1
                    st.markdown(f"<p style='color: green; font-weight: bold;'>Both Models Recommend Layout: {agreed_layout} ⭐</p>", unsafe_allow_html=True)
                # Get bathroom size and windows/doors from session state
                bathroom_size = st.session_state.bathroom_size
                windows_doors = st.session_state.windows_doors
                
                # Create a container for the layout selection
                layout_selection_container = st.container()
                
                with layout_selection_container:
                    # Create columns for layout selection - show up to 3 layouts per row
                    all_scores = st.session_state.layout_scores
                    layout_metrics = st.session_state.layout_metrics
                    
                    # Determine number of rows needed
                    layouts_per_row = 3
                    num_layouts = len(all_scores)
                    num_rows = (num_layouts + layouts_per_row - 1) // layouts_per_row
                    
                    # Display layouts in rows
                    for row in range(num_rows):
                        # Create columns for this row
                        cols = st.columns(layouts_per_row)
                        
                        # Display layouts in this row
                        for col_idx in range(layouts_per_row):
                            layout_idx = row * layouts_per_row + col_idx
                            
                            # Check if we've reached the end of layouts
                            if layout_idx >= num_layouts:
                                break
                                
                            # Get layout data
                            layout, score, detailed_scores = all_scores[layout_idx]
                            
                            with cols[col_idx]:
                                # Create 2D floorplan
                                fig = draw_2d_floorplan(bathroom_size, layout, windows_doors, indoor=True)
                                st.pyplot(fig)
                                
                                # Display score and metrics
                                st.markdown(f"**Layout {layout_idx+1}**")
                                
                                # Highlight recommended layouts
                                ml_recommended = hasattr(st.session_state, 'ml_recommended_layout') and layout_idx == st.session_state.ml_recommended_layout
                                rl_recommended = hasattr(st.session_state, 'rl_recommended_layout') and layout_idx == st.session_state.rl_recommended_layout
                                
                                if ml_recommended and rl_recommended:
                                    st.markdown(f"Score: {score:.1f}/100 ⭐ **Both Models Recommend**")
                                elif ml_recommended:
                                    st.markdown(f"Score: {score:.1f}/100 💡 **ML Recommended**")
                                elif rl_recommended:
                                    st.markdown(f"Score: {score:.1f}/100 🤖 **RL Recommended**")
                                else:
                                    st.markdown(f"Score: {score:.1f}/100")
                                    
                                st.markdown(f"Objects Placed: {layout_metrics[layout_idx]['placed_percentage']:.1f}%")
                                
                                # Add detailed scores in an expandable section
                                with st.expander("View Detailed Scores"):
                                    # Create two columns for better organization of scores
                                    score_cols = st.columns(2)
                                    
                                    # Format and display all detailed scores
                                    sorted_scores = sorted(detailed_scores.items(), key=lambda x: x[1], reverse=True)
                                    for i, (score_name, score_value) in enumerate(sorted_scores):
                                        # Alternate between columns
                                        col_idx = i % 2
                                        with score_cols[col_idx]:
                                            # Format score name for better readability
                                            formatted_name = score_name.replace('_', ' ').title()
                                            # Display score with colored indicator based on value
                                            if score_value >= 8:
                                                st.markdown(f"**{formatted_name}**: :green[{score_value:.1f}]")
                                            elif score_value >= 5:
                                                st.markdown(f"**{formatted_name}**: :orange[{score_value:.1f}]")
                                            else:
                                                st.markdown(f"**{formatted_name}**: :red[{score_value:.1f}]")
                                
                                # Selection button
                                if st.button(f"Select Layout {layout_idx+1}", key=f"select_layout_{layout_idx}"):
                                    st.session_state.selected_layout_index = layout_idx
                                    st.session_state.positions = layout
                                    st.session_state.placed_objects = [pos[5] for pos in layout]
                                    st.session_state.best_layout_score = score
                                    st.session_state.total_score = score
                                    st.session_state.detailed_scores = detailed_scores
                                    
                                    # Add this selection to both models' training data
                                    # Train ML model
                                    st.session_state.ml_model.add_training_example(
                                        layout_idx, 
                                        st.session_state.all_layouts, 
                                        st.session_state.all_scores, 
                                        st.session_state.layout_metrics
                                    )
                                    st.session_state.ml_update_needed = True
                                    
                                    # # Train RL model
                                    try:
                                        # Extract detailed scores from all_scores
                                        # all_scores format: [(layout, score, detailed_scores), ...]
                                        detailed_scores = [item[2] for item in st.session_state.all_scores]
                                        
                                        st.session_state.rl_model.add_training_example(
                                            layout_idx, 
                                            st.session_state.all_layouts, 
                                            [item[1] for item in st.session_state.all_scores],  # Extract scores
                                            detailed_scores,
                                            st.session_state.layout_metrics
                                        )
                                        st.session_state.rl_update_needed = True
                                    except Exception as e:
                                        st.warning(f"RL model training failed: {e}")
                                        st.session_state.rl_update_needed = False
                                    
                                    # Regenerate visualizations for the selected layout
                                    fig_3d = visualize_room_with_shadows_3d(bathroom_size, layout, windows_doors)
                                    st.session_state.fig = fig_3d
                                    
                                    # # Save 3D figure to bytes for download
                                    buf = io.BytesIO()
                                    fig_3d.savefig(buf, format='png', dpi=300, bbox_inches='tight')
                                    buf.seek(0)
                                    st.session_state.fig_bytes = buf.getvalue()
                                    
                                    # Create 2D floorplan
                                    fig_2d = draw_2d_floorplan(bathroom_size, layout, windows_doors, indoor=True)
                                    st.session_state.fig2 = fig_2d
                                    
                                    # Save 2D figure to bytes for download
                                    buf2 = io.BytesIO()
                                    fig_2d.savefig(buf2, format='png', dpi=300, bbox_inches='tight')
                                    buf2.seek(0)
                                    st.session_state.fig2_bytes = buf2.getvalue()
                                    
                                    st.rerun()
            
            # Show the selected layout if one has been chosen
            if st.session_state.selected_layout_index is not None:
                st.success(f"You selected Layout {st.session_state.selected_layout_index + 1} with score: {st.session_state.best_layout_score:.1f}/100")
                
                # Add a button to go back to layout selection
                if st.button("Choose a Different Layout"):
                    st.session_state.selected_layout_index = None
                    st.rerun()
            
            # Only show visualizations if a layout has been explicitly selected
            if st.session_state.selected_layout_index is not None:
                st.markdown("<h3 class='section-header'>Selected Layout Visualization</h3>", unsafe_allow_html=True)
                
                # Section 1: 3D View and 2D Floorplan side by side
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("<p><b>2D Floorplan</b></p>", unsafe_allow_html=True)
                    st.pyplot(st.session_state.fig2)
                    if st.session_state.fig2_bytes is not None:
                        download_button_2d = st.download_button(
                            label="Download 2D Floorplan",
                            data=st.session_state.fig2_bytes,
                            file_name="bathroom_floorplan.png",
                            mime="image/png",
                            key="download_2d"
                        )
                    else:
                        st.warning("2D floorplan download not available")
                        download_button_2d = False
                
                with col2:
                    st.markdown("<p><b>3D Room Layout</b></p>", unsafe_allow_html=True)
                    st.pyplot(st.session_state.fig)
                    if st.session_state.fig_bytes is not None:
                        download_button = st.download_button(
                            label="Download 3D View",
                            data=st.session_state.fig_bytes,
                            file_name="bathroom_3d_view.png",
                            mime="image/png",
                            key="download_3d"
                        )
                    else:
                        st.warning("3D view download not available")
                        download_button = False
                
                if download_button or download_button_2d:
                    st.session_state.download_clicked = True      
                    st.session_state.generate_clicked = False
    
                
                # # Section 2: Available Spaces Analysis side by side
                # st.markdown("<h4 class='section-header'>Available Space Analysis</h4>", unsafe_allow_html=True)
                # col0, col1 ,col2,col3 = st.columns([1,2,2,1])
                
                # with col1:
                #     st.markdown(f"<p><b>With Shadow</b> ({len(st.session_state.available_spaces_dict['with_shadow'])} spaces)</p>", unsafe_allow_html=True)
                #     st.pyplot(st.session_state.figvis_with_shadow)
                
                # with col2:
                #     st.markdown(f"<p><b>Without Shadow</b> ({len(st.session_state.available_spaces_dict['without_shadow'])} spaces)</p>", unsafe_allow_html=True)
                #     st.pyplot(st.session_state.figvis_without_shadow)
                
                # Object placement summary
                st.markdown("<h3 class='section-header'>Fixture Placement Summary</h3>", unsafe_allow_html=True)
                
                # Create a table of placed objects
                if st.session_state.positions:
                    object_data = []
                    for pos in st.session_state.positions:
                        if len(pos) >= 6:
                            object_data.append({
                                "Fixture": pos[5],
                                "Position": f"({pos[0]}, {pos[1]})",
                                "Size": f"{pos[2]}×{pos[3]} cm",
                                "Height": f"{pos[4]} cm"
                            })
                    
                    # Display data
                    st.dataframe(object_data)
            else:
                # Show a message prompting the user to select a layout
                st.info("👆 Please select a layout from above to view detailed visualizations and analysis.")
    
    # Analysis Tab Content
    with tab3:
        if not st.session_state.get('generated', False):
            st.info("Please generate a floorplan first in the Room Setup tab")
        else:
            st.markdown("<h2 class='section-header'>Layout Analysis & ML Insights</h2>", unsafe_allow_html=True)
            
            # Show ML model information
            st.subheader("Machine Learning Model Status")
            
            if st.session_state.ml_model.model is None:
                st.info("The ML model is not yet trained. Select more layouts to train the model.")
                st.markdown(f"Current training examples: {len(st.session_state.ml_model.training_data)}")
                st.markdown("The model needs at least 10 selections to start making recommendations.")
            else:
                st.success("ML model is trained and making recommendations based on your preferences!")
                st.markdown(f"Current training examples: {len(st.session_state.ml_model.training_data)}")
                
                # Show feature importance
                st.subheader("What Influences Your Layout Preferences")
                feature_importance = get_feature_importance(st.session_state.ml_model)
                
                if feature_importance:
                    # Convert to DataFrame for display
                    importance_df = pd.DataFrame(list(feature_importance.items()), 
                                               columns=['Feature', 'Importance'])
                    importance_df = importance_df.sort_values('Importance', ascending=False).head(10)
                    
                    # Clean up feature names for display
                    importance_df['Feature'] = importance_df['Feature'].apply(
                        lambda x: x.replace('score_', '').replace('_', ' ').title()
                    )
                    
                    # Display as bar chart
                    st.bar_chart(importance_df.set_index('Feature'))
                    
                    st.markdown("### Your Layout Preferences")
                    st.markdown("Based on your selections, you seem to prefer layouts with:")
                    
                    # Get top 5 features
                    top_features = importance_df.head(5)['Feature'].tolist()
                    for feature in top_features:
                        st.markdown(f"- Good {feature}")
                        
                    # Reset button
                    if st.button("Reset ML Model"):
                        st.session_state.ml_model = LayoutPreferenceModel()
                        if os.path.exists('layout_preference_model.pkl'):
                            os.remove('layout_preference_model.pkl')
                        st.success("ML model has been reset!")
                        st.rerun()

            # Additional analysis section
            st.markdown("<h2 class='section-header'>Layout Analysis & Optimization</h2>", unsafe_allow_html=True)
            
            # Space utilization metrics
            st.markdown("<h3 class='section-header'>Space Utilization</h3>", unsafe_allow_html=True)
            
            metrics = st.session_state.space_metrics
            total_room_area = metrics["total_room_area"]
            used_area = metrics["used_area"]
            available_area_with_shadow = metrics["available_area_with_shadow"]
            available_area_without_shadow = metrics["available_area_without_shadow"]
            
            
            # Create a more visual metrics display with 4 columns
            metric_cols = st.columns([1,2,2,1])
            
            # Custom metric cards with better alignment
            with metric_cols[0]:
                st.markdown("""
                <div class='metric-card'>
                    <div class='metric-card-label'>Total Room Area</div>
                    <div class='metric-card-value'>{} cm²</div>
                </div>
                """.format(total_room_area), unsafe_allow_html=True)
            
            with metric_cols[1]:
                percentage = int(used_area/total_room_area*100)
                st.markdown("""
                <div class='metric-card'>
                    <div class='metric-card-label'>Used Area</div>
                    <div class='metric-card-value'>{} cm²</div>
                    <div class='metric-card-delta'>{}%</div>
                </div>
                """.format(used_area, percentage), unsafe_allow_html=True)
            
            with metric_cols[2]:
                percentage = int(available_area_with_shadow/total_room_area*100)
                st.markdown("""
                <div class='metric-card'>
                    <div class='metric-card-label'>Available (with shadow)</div>
                    <div class='metric-card-value'>{} cm²</div>
                    <div class='metric-card-delta'>{}%</div>
                </div>
                """.format(available_area_with_shadow, percentage), unsafe_allow_html=True)
            
            with metric_cols[3]:
                percentage = int(available_area_without_shadow/total_room_area*100)
                st.markdown("""
                <div class='metric-card'>
                    <div class='metric-card-label'>Available (no shadow)</div>
                    <div class='metric-card-value'>{} cm²</div>
                    <div class='metric-card-delta'>{}%</div>
                </div>
                """.format(available_area_without_shadow, percentage), unsafe_allow_html=True)
            
            # Layout Comparison (if multiple layouts were generated)
            if 'layout_metrics' in st.session_state:
                st.markdown("<h3 class='section-header'>Layout Comparison</h3>", unsafe_allow_html=True)
                st.info("🔄 Multiple layouts were generated and compared to find the optimal arrangement")
                
                # Show comparison results if available
                layout_metrics = st.session_state.get('layout_metrics', [])
                if layout_metrics:
                    # Create a tab system for different visualization modes
                    comp_tab1, comp_tab2, comp_tab3 = st.tabs(["Score Comparison", "Detailed Metrics", "Layout Analysis"])
                    
                    # Create dataframes for the different metrics
                    layout_labels = [f'Layout {metric["layout_id"]}' for metric in layout_metrics]
                    layout_scores = [metric["score"] for metric in layout_metrics]
                    placed_percentages = [metric["placed_percentage"] for metric in layout_metrics]
                    space_efficiencies = [metric["space_efficiency"] for metric in layout_metrics]
                    
                    with comp_tab1:
                        import pandas as pd
                        import matplotlib.pyplot as plt
                        
                        # Total score comparison
                        st.subheader("Total Layout Quality Scores")
                        
                        # Create dataframe for the scores
                        df = pd.DataFrame({
                            'Layout': layout_labels,
                            'Score': layout_scores
                        })
                        
                        # Create and display chart
                        fig, ax = plt.subplots(figsize=(10, 4))
                        bars = ax.bar(df['Layout'], df['Score'], color='skyblue')
                        
                        # Highlight the best score
                        best_idx = df['Score'].argmax()
                        bars[best_idx].set_color('green')
                        
                        # Add labels and title
                        ax.set_xlabel('Generated Layouts')
                        ax.set_ylabel('Quality Score (0-100)')
                        ax.set_title('Layout Quality Comparison')
                        
                        # Add value labels on top of bars
                        for i, bar in enumerate(bars):
                            height = bar.get_height()
                            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                                    f'{height:.1f}', ha='center', va='bottom')
                        
                        # Add a line for average score
                        avg_score = df['Score'].mean()
                        ax.axhline(y=avg_score, color='red', linestyle='--', alpha=0.7)
                        ax.text(len(df['Layout'])-0.5, avg_score+2, f'Average: {avg_score:.1f}', 
                                color='red', ha='right')
                        
                        st.pyplot(fig)
                    
                    with comp_tab2:
                        # Show metrics as a table
                        st.subheader("Layout Performance Metrics")
                        
                        # Create a dataframe for the metrics table
                        metrics_df = pd.DataFrame({
                            'Layout': layout_labels,
                            'Quality Score': [f"{score:.1f}/100" for score in layout_scores],
                            'Objects Placed': [f"{p:.1f}%" for p in placed_percentages],
                            'Space Efficiency': [f"{e:.1f}%" for e in space_efficiencies]
                        })
                        
                        # Highlight the best row
                        best_idx = layout_scores.index(max(layout_scores))
                        
                        # Show the table with highlighting
                        st.dataframe(metrics_df, use_container_width=True)
                        
                        # Additional comparison metrics
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Create a radar chart for the best layout
                            st.subheader("Best Layout Score Breakdown")
                            best_detailed_scores = layout_metrics[best_idx]["detailed_scores"]
                            
                            # Prepare data for radar chart
                            categories = []
                            values = []
                            
                            for category, score in best_detailed_scores.items():
                                if score > 0:  # Only include scores that have values
                                    cat_name = category.replace('_', ' ').title()
                                    categories.append(cat_name)
                                    values.append(score)
                            
                            # Create radar chart
                            if categories and values:  # Only create if we have data
                                fig = plt.figure(figsize=(6, 6))
                                ax = fig.add_subplot(111, polar=True)
                                
                                # Compute angle for each category
                                angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
                                values.append(values[0])  # Close the polygon
                                angles.append(angles[0])  # Close the polygon
                                categories.append(categories[0])  # For labels
                                
                                # Plot
                                ax.plot(angles, values, 'o-', linewidth=2)
                                ax.fill(angles, values, alpha=0.25)
                                
                                # Set category labels
                                ax.set_xticks(angles[:-1])
                                ax.set_xticklabels(categories[:-1], size=8)
                                
                                # Set radial limits
                                ax.set_ylim(0, 10)
                                
                                st.pyplot(fig)
                        
                        with col2:
                            # Show a table of the detailed scores
                            st.subheader("Score Components")
                            
                            detail_data = []
                            for category, score in best_detailed_scores.items():
                                if score > 0:  # Only include scores that have values
                                    category_name = category.replace('_', ' ').title()
                                    detail_data.append({
                                        "Criterion": category_name,
                                        "Score": f"{score:.2f}/10"
                                    })
                            
                            detail_df = pd.DataFrame(detail_data)
                            st.dataframe(detail_df, use_container_width=True)
                    
                    with comp_tab3:
                        # Show the detailed analysis
                        st.subheader("Layout Component Analysis")
                        
                        # Create a chart showing how different criteria scores vary across layouts
                        # First collect all possible criteria
                        all_criteria = set()
                        for metric in layout_metrics:
                            all_criteria.update(metric["detailed_scores"].keys())
                        
                        # Create a dataframe for all layouts and their criteria scores
                        criteria_data = []
                        for i, metric in enumerate(layout_metrics):
                            layout_dict = {"Layout": f"Layout {metric['layout_id']}"}
                            for criterion in all_criteria:
                                score = metric["detailed_scores"].get(criterion, 0)
                                criterion_name = criterion.replace('_', ' ').title()
                                layout_dict[criterion_name] = score
                            criteria_data.append(layout_dict)
                        
                        criteria_df = pd.DataFrame(criteria_data)
                        
                        # Create a stacked bar chart of all criteria scores by layout
                        if len(criteria_data) > 0 and len(criteria_data[0]) > 1:  # Make sure we have data
                            st.write("Comparing score components across layouts:")
                            
                            # Prepare data for plotting
                            criteria_plot_df = criteria_df.set_index('Layout')
                            
                            # Create plot
                            fig, ax = plt.subplots(figsize=(12, 6))
                            criteria_plot_df.plot(kind='bar', stacked=False, ax=ax)
                            
                            # Add labels and title
                            ax.set_xlabel('Layouts')
                            ax.set_ylabel('Component Scores (0-10)')
                            ax.set_title('Layout Score Component Comparison')
                            ax.legend(title='Criteria', bbox_to_anchor=(1.05, 1), loc='upper left')
                            
                            plt.tight_layout()
                            st.pyplot(fig)
                    
                    # Show best layout details
                    best_score = st.session_state.get('best_layout_score', 0)
                    st.success(f"✓ Selected layout with score: {best_score:.2f}/100")
                    
                    # Show details of what made this layout better
                    if 'detailed_scores' in st.session_state:
                        with st.expander("Why this layout was selected"):
                            st.write("This layout scored highest in the following criteria:")
                            detailed_scores = st.session_state.detailed_scores
                            
                            # Find the top scoring criteria
                            top_criteria = sorted(detailed_scores.items(), key=lambda x: x[1], reverse=True)[:5]
                            
                            for category, score in top_criteria:
                                # Format the category name for better readability
                                category_name = category.replace('_', ' ').title()
                                # Add emoji indicators
                                if score >= 8:  # Excellent score
                                    emoji = "🌟"
                                elif score >= 5:  # Good score
                                    emoji = "✅"
                                else:  # Average or below
                                    emoji = "⚪"
                                st.markdown(f"{emoji} **{category_name}**: {score:.2f}/10")
            
            # # Accessibility analysis
            # st.markdown("<h3 class='section-header'>Accessibility Analysis</h3>", unsafe_allow_html=True)
            
            # # Display warnings about inaccessible spaces
            # if st.session_state.inaccessible_spaces:
            #     st.warning(f"⚠️ There are {len(st.session_state.inaccessible_spaces)} inaccessible spaces in the room layout.")
            #     with st.expander("View inaccessible spaces"):
            #         st.write(st.session_state.inaccessible_spaces)
            # else:
            #     st.success("✅ All spaces in the room are accessible")
            
            # # Display warnings about non-overlapping spaces
            # if st.session_state.non_overlapping_spaces:
            #     st.warning(f"⚠️ There are {len(st.session_state.non_overlapping_spaces)} non-overlapping spaces that may be isolated.")
            #     with st.expander("View non-overlapping spaces"):
            #         st.write(st.session_state.non_overlapping_spaces)
            
            # Layout quality score
            st.markdown("<h3 class='section-header'>Layout Quality Score</h3>", unsafe_allow_html=True)
            
            
            total_score = st.session_state.total_score
            # only 3 decimal places
            total_score = round(total_score, 3)
            st.markdown(f"<div style='text-align: left; font-size: 3rem; font-weight: bold; color: {'green' if total_score > 70 else 'orange' if total_score > 40 else 'red'};'>{total_score}/100</div>", unsafe_allow_html=True)
            # Display detailed scores
            detailed_scores = st.session_state.detailed_scores
            for category, score in detailed_scores.items():
                st.markdown(f"**{category}**: {score}/10")


            # Add pathway accessibility analysis
            # accessibility_score = st.session_state.detailed_scores["pathway_accessibility"]
            # # Analyze pathway accessibility
            # pathway_fig = analyze_pathway_accessibility(
            #     st.session_state.positions, 
            #     st.session_state.bathroom_size, 
            #     st.session_state.windows_doors,
            #     path_width
            # )
            
            # Display the accessibility score
            # st.markdown(f"<p>Accessibility Score: <strong>{accessibility_score:.1f}/10</strong></p>", unsafe_allow_html=True)
            
            # Explanation of the score
            # if accessibility_score >= 8:
            #     st.success("Great accessibility! Most fixtures can be reached with comfortable pathways.")
            # elif accessibility_score >= 5:
            #     st.info("Acceptable accessibility. Some fixtures may be difficult to access.")
            # else:
            #     st.warning("Poor accessibility. Consider rearranging fixtures to improve pathways.")
            col1, col2, col3 = st.columns([1, 1, 1])   
            # Display the pathway visualization
            #col2.pyplot(pathway_fig)
            
            # Suggestions for improvement
            #st.markdown("<h3 class='section-header'>Suggested Improvements</h3>", unsafe_allow_html=True)
            
            # Button to suggest additional fixtures
            #suggest_col1, suggest_col2, suggest_col3 = st.columns([1, 2, 1])
            
            # with suggest_col2:
            #     suggest_button = st.button(
            #         "Suggest Additional Fixtures", 
            #         use_container_width=True,
            #         type="secondary",
            #         key="suggest_fixtures_button"
            #     )
            
            # # Handle fixture suggestions
            # if suggest_button:
            #     with st.spinner("Analyzing available spaces and suggesting fixtures..."):
            #         suggestions = suggest_additional_fixtures(
            #             st.session_state.positions, 
            #             st.session_state.bathroom_size, 
            #             OBJECT_TYPES, 
            #             st.session_state.available_spaces_dict['with_shadow'], 
            #             st.session_state.available_spaces_dict['without_shadow']
            #         )
            #         st.session_state.suggestions = suggestions
                    
            #         if suggestions["message"] != "No suitable fixtures can be added to the available spaces":
            #             fixture_options = list(suggestions["suggestions"].keys())
            #             st.session_state.fixture_options = fixture_options
            #             st.session_state.selected_fixtures = fixture_options[:min(2, len(fixture_options))]
                        
            #             st.success(f"Found {len(fixture_options)} potential fixtures that could be added!")
            #         else:
            #             st.info("No additional fixtures can be added to the available spaces")
            
            # # Display fixture suggestions if available
            # if "suggestions" in st.session_state:
            #     if st.session_state.suggestions["message"] != "No suitable fixtures can be added to the available spaces":
            #         fixture_options = st.session_state.fixture_options
                    
            #         st.markdown("<h4>Select fixtures to add:</h4>", unsafe_allow_html=True)
            #         selected_fixtures = st.multiselect(
            #             "Additional fixtures", 
            #             options=fixture_options, 
            #             default=st.session_state.selected_fixtures,
            #             key="fixture_multiselect"
            #         )
            #         st.session_state.selected_fixtures = selected_fixtures
                    
            #         # Button to add selected fixtures
            #         add_col1, add_col2, add_col3 = st.columns([1, 2, 1])
                    
            #         with add_col2:
            #             add_button = st.button(
            #                 "Add Selected Fixtures", 
            #                 use_container_width=True,
            #                 type="primary",
            #                 key="add_fixtures_button",
            #                 disabled=not selected_fixtures
            #             )
                    
            #         # Handle adding fixtures
            #         if add_button and selected_fixtures:
            #             with st.spinner("Adding fixtures to layout..."):
            #                 updated_positions, added_objects = add_objects_to_available_spaces(
            #                     st.session_state.positions, 
            #                     st.session_state.bathroom_size, 
            #                     OBJECT_TYPES,
            #                     priority_objects=selected_fixtures,
            #                     available_spaces=st.session_state.available_spaces_dict['with_shadow']
            #                 )
                            
            #                 if added_objects:
            #                     st.success(f"✅ Successfully added {len(added_objects)} new fixtures to the layout!")
                                
            #                     # Update positions and recalculate everything
            #                     positions = updated_positions + st.session_state.positions
            #                     st.session_state.positions = positions
                                
            #                     # Update available spaces
            #                     available_spaces_dict = identify_available_space(
            #                         positions, 
            #                         st.session_state.bathroom_size, 
            #                         windows_doors=st.session_state.windows_doors
            #                     )
            #                     st.session_state.available_spaces_dict = available_spaces_dict
                                
            #                     # Update visualizations
            #                     fignew = visualize_room_with_shadows_3d(st.session_state.bathroom_size, positions, st.session_state.windows_doors)
            #                     st.session_state.fig = fignew
                                
            #                     fignew2 = draw_2d_floorplan(st.session_state.bathroom_size, positions, st.session_state.windows_doors, selected_door_way)
            #                     st.session_state.fig2 = fignew2
                                
            #                     fignewvis = visualize_room_with_available_spaces(positions, st.session_state.bathroom_size, available_spaces_dict['with_shadow'], shadow=True)
            #                     st.session_state.figvis_with_shadow = fignewvis
                                
            #                     fignewvis2 = visualize_room_with_available_spaces(positions, st.session_state.bathroom_size, available_spaces_dict['without_shadow'], shadow=False)
            #                     st.session_state.figvis_without_shadow = fignewvis2
                                
            #                     # Show updated visualizations
            #                     st.subheader("Updated 3D Layout")
            #                     st.pyplot(fignew)
                                
            #                     st.subheader("Updated 2D Floorplan")
            #                     st.pyplot(fignew2)
            #                 else:
            #                     st.warning("Could not add any of the selected fixtures due to space constraints.")
    
    # Review Tab Content
    with tab4:
        if not st.session_state.get('generated', False):
            st.info("Please generate a floorplan first in the Room Setup tab")
        else:
            st.markdown("<h2 class='section-header'>Review & Save Your Design</h2>", unsafe_allow_html=True)
            
            review_col1, review_col2, review_col3 = st.columns([2,1,1])
            
            with review_col1:
                # Create a form for the review
                with st.form(key="review_form"):
                    st.markdown("<h3 class='section-header'>Rate Your Design</h3>", unsafe_allow_html=True)
                    
                    # Room name input
                    room_name = st.text_input("Room Name", "My Bathroom Design")
                
                    # Rating section with columns
                    rating_col1, rating_col2 = st.columns(2)
                    
                    with rating_col1:
                        is_enough_path = st.checkbox("Is there enough pathway space?", value=True)
                        is_everything = st.checkbox("Is everything placed correctly?", value=True)
                    
                    with rating_col2:
                        # make radiobuttons
                        st.markdown("<h4>Space Utilization</h4>", unsafe_allow_html=True, help="Rate how well the space is utilized")
                        space = st.radio("Rate how well the space is utilized", [1,2,3,4,5], index=2, horizontal=True, label_visibility="collapsed")
                        st.markdown("<h4>Overall Satisfaction</h4>", unsafe_allow_html=True, help="Rate your overall satisfaction with the design")
                        overall = st.radio("Rate your overall satisfaction with the design", [1,2,3,4,5], index=2, horizontal=True, label_visibility="collapsed")
                        st.markdown("<h4> The calculated reward should be lower, higher or optimal?</h4>", unsafe_allow_html=True, help="Select lower if the calculated reward is higher than the optimal reward, select higher if the calculated reward is lower than the optimal reward, select optimal if the calculated reward is optimal")
                        reward = st.radio("The calculated reward should be lower, higher or optimal?", ["lower", "higher", "optimal"], index=2, horizontal=True, label_visibility="collapsed")
                        
                    
                    # Review text
                    st.markdown("<h3 class='section-header'>Your Feedback</h3>", unsafe_allow_html=True)
                    review = st.text_area(
                        "Write your review about the generated room:", 
                        "I like the layout of the bathroom. The objects are well-positioned and there's enough space to move around.",
                        height=150
                    )
                    
                    # Submit button
                    submit_button = st.form_submit_button(
                        "Submit Review", 
                        use_container_width=True,
                        type="primary"
                    )
                
                # Handle review submission
                if submit_button:
                    calculated_reward = st.session_state.total_score
                    with st.spinner("Saving your review..."):
                        success = save_data(
                            supabase,
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
                        
                        if success:
                            st.balloons()
                            st.success("Thank you for your review! Your design has been saved to the database.")
                            
                            
                        else:
                            st.error("Failed to save your review. Please try again.")
                            # Design summary
                # st.markdown("<h3 class='section-header'>Design Summary</h3>", unsafe_allow_html=True)
                
                # summary_col1, summary_col2 = st.columns(2)
                
                # with summary_col1:
                #     st.markdown("<h4>Room Dimensions</h4>", unsafe_allow_html=True)
                #     st.markdown(f"Width: **{room_width} cm**")
                #     st.markdown(f"Depth: **{room_depth} cm**")
                #     st.markdown(f"Height: **{room_height} cm**")
                #     st.markdown(f"Total Area: **{room_width * room_depth} cm²**")
                    
                #     st.markdown("<h4>Door Details</h4>", unsafe_allow_html=True)
                #     st.markdown(f"Position: **{selected_door_type}**")
                #     st.markdown(f"Width: **{door_width} cm**")
                #     st.markdown(f"Height: **{door_height} cm**")
                #     st.markdown(f"Swing: **{selected_door_way}**")
            
            with review_col2:
                st.markdown("<p><b>2D Floorplan</b></p>", unsafe_allow_html=True)
                if 'fig2' in st.session_state:
                    st.pyplot(st.session_state.fig2)
                    if 'fig2_bytes' in st.session_state and st.session_state.fig2_bytes is not None:
                        download_button_2d = st.download_button(
                            label="Download 2D Floorplan",
                            data=st.session_state.fig2_bytes,
                            file_name="bathroom_floorplan.png",
                            mime="image/png",
                            key="download_2d_review"
                        )
                    else:
                        st.warning("2D floorplan download not available")
                        download_button_2d = False
                else:
                    st.info("2D floorplan visualization not available")
                    download_button_2d = False
            
            with review_col3:
                # Layout quality score
                st.markdown("<h3 class='section-header'>Layout Quality Score</h3>", unsafe_allow_html=True)
                

                total_score = st.session_state.total_score
                # only 3 decimal places
                total_score = round(total_score, 3)
                st.markdown(f"<div style='text-align: left; font-size: 3rem; font-weight: bold; color: {'green' if total_score > 70 else 'orange' if total_score > 40 else 'red'};'>{total_score}</div>", unsafe_allow_html=True)
                
                # Display detailed scores
                detailed_scores = st.session_state.detailed_scores
                for category, score in detailed_scores.items():
                        st.markdown(f"**{category}**: {score}/10")

                # write out room data json
                room_data = {
                    "room_width": room_width,
                    "room_depth": room_depth,
                    "room_height": room_height,
                    "positions": st.session_state.positions,
                    "windows_doors": st.session_state.windows_doors,
                    "review": review,
                    "is_enough_path": is_enough_path,
                    "space": space,
                    "overall": overall,
                    "is_everything": is_everything
                }
                with open("room_data.json", "w") as f:
                    json.dump(room_data, f)
            
            

            



            



   







    # if st.button("Suggest Fixtures"):	
    #     suggestions = []
    #     available_spaces_dict = st.session_state.available_spaces_dict
    #     positions = st.session_state.positions
    #     bathroom_size = st.session_state.bathroom_size
    #     #if 'suggestions' not in st.session_state:
    #     suggestions = suggest_additional_fixtures(positions, bathroom_size, OBJECT_TYPES, available_spaces_dict['with_shadow'], available_spaces_dict['without_shadow'])
    #     st.session_state.suggestions = suggestions
    #     fixture_options = list(suggestions["suggestions"].keys())
    #     st.session_state.fixture_options = fixture_options
    #     selected_fixtures = fixture_options[:min(2, len(fixture_options))]
    #     st.session_state.selected_fixtures = selected_fixtures

    # # Get suggestions first
    # if "suggestions" in st.session_state:
    #     st.subheader("Suggested Additional Fixtures")
    #     if st.session_state.suggestions["message"] != "No suitable fixtures can be added to the available spaces":
    #         # Create a selection for the user
    #         fixture_options = st.session_state.fixture_options
    #         selected_fixtures = st.multiselect("Select additional fixtures to add", options=fixture_options, default=st.session_state.selected_fixtures)
    #         st.session_state.selected_fixtures = selected_fixtures
       
    # # Always show the button if there are fixture options
    # add_button = st.button("Add Selected Fixtures")
                
    # if st.session_state.selected_fixtures and add_button:
    #     # Add selected fixtures to the layout
    #     updated_positions, added_objects = add_objects_to_available_spaces(
    #             positions, 
    #             (room_width, room_depth), 
    #             OBJECT_TYPES,
    #             priority_objects=st.session_state.selected_fixtures,
    #             available_spaces=st.session_state.available_spaces_dict['with_shadow']
    #         )

    #     if added_objects:
    #         st.success(f"Added {len(added_objects)} new fixtures to the layout!")
    #         positions = updated_positions + st.session_state.positions
    #         windows_doors = st.session_state.windows_doors  
                        
    #         # Update available spaces after adding objects
    #         available_spaces_dict = identify_available_space(positions, (room_width, room_depth),  windows_doors=windows_doors) #true
    #         fignew = visualize_room_with_shadows_3d((room_width, room_depth), positions, windows_doors)
    #         st.pyplot(fignew)
    #         fignew2 = draw_2d_floorplan((room_width, room_depth), positions, windows_doors, selected_door_way)
    #         st.pyplot(fignew2)
    #         fignewvis = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces_dict['with_shadow'], shadow=True)
    #         st.pyplot(fignewvis)
    #         fignewvis2 = visualize_room_with_available_spaces(positions, (room_width, room_depth), available_spaces_dict['without_shadow'], shadow=False)
    #         st.pyplot(fignewvis2)
    #         st.session_state.new_positions = positions
    #         st.session_state.fignew = fignew
    #         st.session_state.fignew2 = fignew2
    #         st.session_state.fignewvis = fignewvis
    #         st.session_state.fignewvis2 = fignewvis2
            
            
    #     else:
    #         st.warning("Could not add any of the selected fixtures due to space constraints.")
		
		
    # is_enough_path = st.checkbox("Is there enough pathway space?")
    # is_everything = st.checkbox("Is everything placed?")
    
    # # Space Utilization rating with radio buttons
    # st.markdown("<h4>Space Utilization:</h4>", unsafe_allow_html=True)
    # space_options = ["Very Bad", "Bad", "Average", "Good", "Very Good"]
    # space_values = {option: i*2.5 for i, option in enumerate(space_options)}
    
    # # Use radio buttons instead of checkboxes
    # space_selection = st.radio(
    #     "Rate the space utilization:",
    #     space_options,
    #     index=2,  # Default to "Average"
    #     horizontal=True,
    #     label_visibility="collapsed"
    # )
    
    # # Convert selection to numeric value (0-10 scale)
    # space = space_values.get(space_selection, 5)
    
    # # Overall Satisfaction rating with radio buttons
    # st.markdown("<h4>Overall Satisfaction:</h4>", unsafe_allow_html=True)
    # overall_options = ["Very Bad", "Bad", "Average", "Good", "Very Good"]
    # overall_values = {option: i*2.5 for i, option in enumerate(overall_options)}
    
    # # Use radio buttons instead of checkboxes
    # overall_selection = st.radio(
    #     "Rate your overall satisfaction:",
    #     overall_options,
    #     index=2,  # Default to "Average"
    #     horizontal=True,
    #     label_visibility="collapsed"
    # )
    
    # # Convert selection to numeric value (0-10 scale)
    # overall = overall_values.get(overall_selection, 5)
    
    # st.write("Write your review about the generated room:")
    # review = st.text_area("Review", "Write your review here...")
    # if st.button("Submit Review"):
    #     # Set a flag to indicate we're submitting a review
    #     st.session_state.review_submitted = True
    #     save_data((room_width, room_depth, room_height), st.session_state.positions, st.session_state.windows_doors, review, is_enough_path, space, overall, is_everything)
    #     st.success("Thank you for your review, all data saved to database!")
        
    # Saved Reviews Tab Content
    with tab5:
        st.markdown("<h2 class='section-header'>Saved Bathroom Reviews</h2>", unsafe_allow_html=True)
        
        # Add a reload button at the top
        if st.button("🔄 Reload Reviews", key="reload_reviews"):
            # Force a rerun of the app to refresh the reviews
            st.rerun()
        
        st.markdown("*Click the button above to refresh the list of saved reviews*")
        
        if not st.session_state.saved_reviews:
            st.info("No saved reviews found. Generate and save a layout to see it here.")
        else:
            # Display number of saved reviews
            st.markdown(f"<p>Found {len(st.session_state.saved_reviews)} saved reviews</p>", unsafe_allow_html=True)
            
            # Sort reviews by created_at timestamp if available, otherwise use the current order
            # Format will be newest first (latest timestamp), oldest last
            sorted_reviews = sorted(
                st.session_state.saved_reviews,
                key=lambda x: x.get('created_at', 0),  # Default to 0 if timestamp doesn't exist
                reverse=True 
            )
            
            # Create an expander for each review in timestamp order
            for i, review in enumerate(sorted_reviews):
                # Create a unique ID for this review
                review_id = f"review_{i}"
                
                # Create an expander for this review
                with st.expander(f"{review.get('room_name')} - {review.get('room_width')}×{review.get('room_depth')}cm Room"):
                    # Create two columns for layout details and floorplan/controls
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # Room dimensions
                        st.markdown("<h4>Room Dimensions</h4>", unsafe_allow_html=True)
                        st.markdown(f"**Width:** {review.get('room_width', 'N/A')} cm")
                        st.markdown(f"**Depth:** {review.get('room_depth', 'N/A')} cm")
                        st.markdown(f"**Height:** {review.get('room_height', 'N/A')} cm")
                        
                        # Objects in the room
                        st.markdown("<h4>Objects</h4>", unsafe_allow_html=True)
                        objects = review.get('objects', [])
                        if objects:
                            for obj in objects:
                                st.markdown(f"• **{obj.get('name', 'Unknown')}** ({obj.get('width', 'N/A')}×{obj.get('depth', 'N/A')}×{obj.get('height', 'N/A')} cm)")
                        else:
                            st.markdown("No objects found in this review.")
                        
                        # User review text
                        if review.get('review') and review.get('review').get('text'):
                            st.markdown("<h4>User Comments</h4>", unsafe_allow_html=True)
                            st.markdown(f"*{review.get('review').get('text')}*")
                        
                        # Ratings if available
                        ratings_available = all(key in review for key in ['space', 'overall', 'is_enough_path'])
                        if ratings_available:
                            st.markdown("<h4>Ratings</h4>", unsafe_allow_html=True)
                            st.markdown(f"**Space Utilization:** {review.get('space', 'N/A')}/10")
                            st.markdown(f"**Overall Satisfaction:** {review.get('overall', 'N/A')}/10")
                            st.markdown(f"**Enough Pathway Space:** {'Yes' if review.get('is_enough_path') else 'No'}")
                            st.markdown(f"**Everything Placed:** {'Yes' if review.get('is_everything') else 'No'}")
                            st.markdown(f"**Reward:** {review.get('reward', 'N/A')}")
                            st.markdown(f"**Calculated Reward:** {review.get('calculated_reward', 'N/A')}")
                    
                    with col2:
                        # Generate and display 2D floorplan
                        st.markdown("<h4>2D Floorplan</h4>", unsafe_allow_html=True)
                        
                        # Automatically show the floorplan when expander is opened
                        # Render the floorplan as an image
                        with st.spinner("Rendering floorplan..."):
                            img, img_bytes = render_saved_floorplan(review)
                            if img and img_bytes:
                                # Display the image
                                st.image(img_bytes, caption=f"Floorplan for {review.get('room_width')}×{review.get('room_depth')}cm Room")
                                
                                # Add download button
                                st.download_button(
                                    label="Download Floorplan",
                                    data=img_bytes,
                                    file_name=f"floorplan_{i+1}.png",
                                    mime="image/png",
                                    key=f"download_floorplan_{i}"
                                )
                            else:
                                st.warning("Could not render floorplan for this review.")
