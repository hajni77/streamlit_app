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
import psycopg2
import gc
from st_supabase_connection import SupabaseConnection

from layout_ml import LayoutPreferenceModel, get_feature_importance
from layout_rl import LayoutRLModel
from utils.helpers import get_required_area, identify_available_space, mark_inaccessible_spaces, check_valid_room, check_overlap
from optimization import compare_room_layouts
from optimization.scoring import BathroomScoringFunction
from matplotlib import patches
from authentication import auth_section
from models.windows_doors import WindowsDoors
from models.object import BathroomObject
from models.bathroom import Bathroom
from visualization import Visualizer2D, draw_door, Visualizer3D
# Import the new validation system
from validation import get_constraint_validator
from algorithms.beam_search import BeamSearch
from models.layout import Layout

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

# Function to display layouts as 2D floorplans with selection buttons
def display_layout_selection(layouts, room_width, room_depth, room_height, windows_doors, layout_metrics=None, ml_recommended=None, rl_recommended=None):
    """
    Display multiple layouts as 2D floorplans with selection buttons.
    
    Args:
        layouts: List of layout tuples (layout, score, detailed_scores)
        room_width: Width of the room in cm
        room_depth: Depth of the room in cm
        room_height: Height of the room in cm
        windows_doors: Windows and doors configuration
        layout_metrics: Optional metrics for each layout
        ml_recommended: Optional index of ML model recommended layout
        rl_recommended: Optional index of RL model recommended layout
        
    Returns:
        int or None: Index of selected layout or None if no selection made
    """
    # Determine number of rows needed (3 layouts per row)
    layouts_per_row = 3
    num_layouts = len(layouts)
    num_rows = (num_layouts + layouts_per_row - 1) // layouts_per_row
    
    # Display recommendations if available
    if ml_recommended is not None:
        st.markdown(f"<p>ML Model Recommended Layout: {ml_recommended + 1}</p>", unsafe_allow_html=True)
    
    if rl_recommended is not None:
        st.markdown(f"<p>RL Model Recommended Layout: {rl_recommended + 1}</p>", unsafe_allow_html=True)
    
    # If both models agree on a recommendation, highlight it
    if ml_recommended is not None and rl_recommended is not None and ml_recommended == rl_recommended:
        st.markdown(f"<p style='color: green; font-weight: bold;'>Both Models Recommend Layout: {ml_recommended + 1} ⭐</p>", unsafe_allow_html=True)
    
    selected_layout_index = None
    
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
            
            # Get the current layout data
            layout_data = layouts[layout_idx]
            if isinstance(layout_data, tuple) and len(layout_data) >= 3:
                bathroom, score, detailed_scores = layout_data
            else:
                # Fallback for object format
                bathroom = layout_data.bathroom if hasattr(layout_data, 'bathroom') else []
                score = layout_data.score if hasattr(layout_data, 'score') else 0
                detailed_scores = layout_data.score_breakdown if hasattr(layout_data, 'score_breakdown') else {}
                
            # Create bathroom object if it's not already one
            if not hasattr(bathroom, 'objects'):
                # If bathroom is just a list of objects
                bathroom = Bathroom(room_width, room_depth, room_height, bathroom, windows_doors, OBJECT_TYPES)
            else:
                # Only keep valid bathroom objects
                bathroom.objects = [obj for obj in bathroom.objects if not isinstance(obj, BathroomObject)]
                bathroom = Bathroom(room_width, room_depth, room_height, bathroom.objects, windows_doors, OBJECT_TYPES)
            with cols[col_idx]:
                
                temp_visualizer = Visualizer2D(bathroom)
                fig = temp_visualizer.draw_2d_floorplan()
                
                # Display the 2D floorplan
                st.pyplot(fig)
                
                # Display layout number and score
                st.markdown(f"**Layout {layout_idx+1}**")
                
                # Highlight recommended layouts
                is_ml_recommended = ml_recommended is not None and layout_idx == ml_recommended
                is_rl_recommended = rl_recommended is not None and layout_idx == rl_recommended
                
                # Format score display
                score_display = f"{score:.1f}/100" if isinstance(score, (int, float)) else "N/A"
                
                # Add recommendation badges
                if is_ml_recommended and is_rl_recommended:
                    st.markdown(f"Score: {score_display} ⭐ **Both Models Recommend**")
                elif is_ml_recommended:
                    st.markdown(f"Score: {score_display} 💡 **ML Recommended**")
                elif is_rl_recommended:
                    st.markdown(f"Score: {score_display} 🤖 **RL Recommended**")
                else:
                    st.markdown(f"Score: {score_display}")
                
                # Display layout metrics if available
                if layout_metrics and layout_idx < len(layout_metrics) and 'placed_percentage' in layout_metrics[layout_idx]:
                    placed_percentage = layout_metrics[layout_idx]['placed_percentage']
                    if isinstance(placed_percentage, (int, float)):
                        st.markdown(f"Objects Placed: {placed_percentage:.1f}%")
                    else:
                        st.markdown(f"Objects Placed: {placed_percentage}%")
                else:
                    st.markdown("Objects Placed: N/A")
                
                # Add detailed scores in an expandable section
                with st.expander("View Detailed Scores"):
                    # Create two columns for better organization of scores
                    score_cols = st.columns(2)
                    
                    # Format and display all detailed scores if available
                    if detailed_scores and isinstance(detailed_scores, dict) and detailed_scores:
                        sorted_scores = sorted(detailed_scores.items(), key=lambda x: x[1], reverse=True)
                        for i, (score_name, score_value) in enumerate(sorted_scores):
                            # Alternate between columns
                            col_idx = i % 2
                            with score_cols[col_idx]:
                                # Format score name for better readability
                                formatted_name = score_name.replace('_', ' ').title()
                                # Display score with colored indicator based on value
                                if isinstance(score_value, (int, float)):
                                    if score_value >= 8:
                                        st.markdown(f"**{formatted_name}**: :green[{score_value:.1f}]")
                                    elif score_value >= 5:
                                        st.markdown(f"**{formatted_name}**: :orange[{score_value:.1f}]")
                                    else:
                                        st.markdown(f"**{formatted_name}**: :red[{score_value:.1f}]")
                                else:
                                    st.markdown(f"**{formatted_name}**: {score_value}")
                    else:
                        st.info("No detailed scores available for this layout.")
                
                # Selection button
                if st.button(f"Select Layout {layout_idx+1}", key=f"select_layout_{layout_idx}"):
                    selected_layout_index = layout_idx
                    print(selected_layout_index)
                    st.session_state.selected_layout_index = selected_layout_index
    
    return selected_layout_index

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


# Helper: get user-bound supabase client
def get_user_supabase():
    token = st.session_state.get('access_token')
    if token:
        return create_client(st.secrets['SUPABASE_URL'], token)
    return supabase  # fallback to anon/service

# Load object types
OBJECT_TYPES = []
with open('object_types.json') as f:
    OBJECT_TYPES = json.load(f)
# Define objects from object_types.json
object_list = [{'id': key, **value} for key, value in OBJECT_TYPES.items()]

common_fixtures = [obj['name'] for obj in object_list]

st.session_state.common_fixtures = common_fixtures

# Initialize constraint validator for the bathroom
default_validator = get_constraint_validator(room_type="bathroom")

# Define constants for the app
door_images = { 
    "top" : "front.png",
    "left" : "left.png",
    "right" : "right.png",
    "bottom" : "back.png", 
}
objects_map = {}
for obj in object_list:
    objects_map[obj['name']] = obj['name'].lower()
objects_map = { 
    "Bathtub": "bathtub",
    "Sink": "sink",
    "Washing Machine": "washing machine",
    "Toilet": "toilet",
    "Shower": "shower",
    "Double Sink": "double sink",
    "Cabinet": "cabinet",
    "Washing Dryer": "washing dryer",
    "Washing Machine Dryer": "washing machine dryer",
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
                # MINDEN TÖRÖLHETŐ
    
                fig = draw_door(selected_door_type, selected_door_way, selected_door_hinge, x, door_width, door_height, room_width, room_depth)
                plt.tight_layout()
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
                
                                

            
        
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
        required_area = get_required_area(selected_object, room_width, room_depth,OBJECT_TYPES)
        
        # If room is too small for all objects, return None to indicate error
        if required_area > room_area * 0.9:  # Leave at least 10% for maneuvering
            print(f"ERROR: Room too small for all requested objects. Need {required_area:.2f} cm² but only have {room_area} cm²")
            st.error(f"ERROR: Room too small for all requested objects. Need {required_area:.2f} cm² but only have {room_area} cm²")

        
        # Show a progress bar during generation
        with st.spinner("Generating your 3D floorplan..."):
            st.session_state.generated = True
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
            #default door depth value
            door_depth = 5  
            # Map selected objects to internal names
            selected_objects = [objects_map[obj] for obj in selected_object]
            st.session_state.selected_objects = selected_objects
            windows_doors = WindowsDoors("door1", selected_door_type,  (x, y), door_width, door_depth, door_height, selected_door_hinge, selected_door_way)
            st.session_state.windows_doors = windows_doors
            # Create room objects
            objects = [BathroomObject(obj) for obj in selected_objects]
            room = Bathroom(room_width, room_depth, room_height, objects, windows_doors, OBJECT_TYPES)
            

            
            # Set bathroom dimensions
            bathroom_size = room.get_size()
            
            # Generate multiple room layouts and select the best one
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            # Number of layouts to generate
            num_layouts = 1
            
            # Store all generated layouts
            all_layouts = []
            layout_scores = []
            
            progress_text.text(f"Generating {num_layouts} different room layouts...")
            
            # Generate multiple layouts
            for i in range(num_layouts):
                progress_text.text(f"Generating layout {i+1}/{num_layouts}...")
                progress_bar.progress((i / num_layouts) *0.6 )  # Use 60% of progress bar for generation
                # generate layout using beam search, give the beam_width best layouts
                layout_positions = BeamSearch(room, selected_objects, beam_width=20).generate(selected_objects, windows_doors)
 
                # Generate a layout
                #layout_positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES, attempt=10000)
                if layout_positions is None:
                    st.error("Room too small for all objects.")
                    break

                for i in layout_positions:
                    all_layouts.append(i)
                # gc collect beamsearch
                #gc.collect()
            
            # If we have layouts, show all of them for user selection
            if all_layouts:
                progress_text.text("Evaluating all layouts...")
                progress_bar.progress(0.7)  # 70% progress
                
                # compare all layouts
                sorted_layouts = compare_room_layouts(
                    all_layouts, 

                )
                

                


                
                # Use the best layout
                # progress_text.text(f"Selected best layout with score: {best_score:.2f}/100")
                # progress_bar.progress(0.9)  # 90% progress
                # positions = best_layout
                # placed_objects = [pos[5] for pos in positions]
                all_scores = []
                all_detailed_scores = []
                for i in sorted_layouts:

                    placed_objects = i.bathroom.get_placed_objects()
                    score = i.score
                    detailed_scores = i.score_breakdown
                    all_scores.append(score)
                    all_detailed_scores.append(detailed_scores)

                # Store all scores and best layout in session state
                # Store enriched scores data format: [(layout, score, detailed_scores), ...]
                st.session_state.layout_scores = all_scores
                st.session_state.all_layouts = sorted_layouts
                st.session_state.all_scores = all_detailed_scores
                
                positions = []
                for i in sorted_layouts:
                    
                    bathroom = i.bathroom.get_placed_objects()
                    positions.append(bathroom)
                #st.session_state.best_layout_score = best_score
                #st.session_state.total_score = best_score  # Update the main score variable
                st.session_state.positions = positions
                # Extract layout performance metrics
                room_width, room_depth , room_height = bathroom_size
                layout_metrics = []
                
                for i, layout in enumerate(sorted_layouts):
                    # Calculate object placement percentage
                    placed_objects_count = len(layout.bathroom.get_placed_objects())
                    placement_percentage = (placed_objects_count / len(selected_objects)) * 100 if selected_objects else 100
                    
                    # Calculate space efficiency
                    total_area = room_width * room_depth


                    used_area = sum(obj['position'][2] * obj['position'][3] for obj in layout.bathroom.get_placed_objects())  # width * depth
                    space_efficiency = (used_area / total_area) * 100
                    
                    # Store metrics
                    layout_metrics.append({
                        "layout_id": i + 1,  # 1-based indexing for display
                        "score": layout.score,  # Default score since we don't have individual scores
                        "placed_percentage": placement_percentage,
                        "space_efficiency": space_efficiency,
                        "detailed_scores": layout.score_breakdown  # Empty detailed scores
                    })
                
                st.session_state.layout_metrics = layout_metrics
                
                # # Use ML model to predict the best layout if available
                # if st.session_state.ml_model.model is not None:
                #     try:
                #         # The ML model expects all_scores in the format [(layout, score, detailed_scores), ...]
                #         ml_best_idx = st.session_state.ml_model.predict_best_layout(all_layouts, all_scores, layout_metrics)
                #         # Store the ML recommendation
                #         st.session_state.ml_recommended_layout = ml_best_idx
                #     except Exception as e:
                #         st.warning(f"ML model prediction failed: {e}")
                #         st.session_state.ml_recommended_layout = None
                
                # # Use RL model to predict the best layout if available
                # if hasattr(st.session_state, 'rl_model') and st.session_state.rl_model is not None:
                #     try:
                #         # Extract the required data from all_scores
                #         # all_scores format: [(layout, score, detailed_scores), ...]
                #         layouts = [item[0] for item in all_scores]
                #         scores = [item[1] for item in all_scores]
                #         detailed_scores = [item[2] for item in all_scores]
                        
                #         rl_best_idx = st.session_state.rl_model.predict_best_layout(layouts, scores, detailed_scores, layout_metrics)
                #         # Store the RL recommendation
                #         st.session_state.rl_recommended_layout = rl_best_idx
                #     except Exception as e:
                #         st.warning(f"RL model prediction failed: {e}")
                #         st.session_state.rl_recommended_layout = None
                
                # Display all layouts as 2D floorplans for selection
                # progress_text.text("Select your preferred layout:")
                # progress_bar.progress(0.9)  # 90% progress
                
                # # Create a container for the layout selection
                # layout_selection_container = st.container()
                
                # with layout_selection_container:
                #     st.markdown("<h3 class='section-header'>Select Your Preferred Layout</h3>", unsafe_allow_html=True)
                #     # Display layouts as 2D floorplans with selection buttons
                #     #NM EZ AZ 
                #     selected_layout_index = display_layout_selection(
                #         st.session_state.all_layouts,
                #         room_width,
                #         room_depth,
                #         room_height,
                #         windows_doors,
                #         layout_metrics=layout_metrics,
                #         ml_recommended=None,  # Add ML recommendations if available
                #         rl_recommended=None   # Add RL recommendations if available
                #     )
                
                    
                #     # If a layout is selected, use it
                #     if selected_layout_index is not None:
                #         print(selected_layout_index)
                #         positions = all_scores[selected_layout_index][0]
                #         placed_objects = [pos[5] for pos in positions]
                #         best_score = all_scores[selected_layout_index][1]
                #         detailed_scores = all_scores[selected_layout_index][2]
                #         st.session_state.selected_layout_index = selected_layout_index
                #         st.session_state.best_layout_score = best_score
                #         st.session_state.total_score = best_score  # Update the main score variable
                #         st.session_state.detailed_scores = detailed_scores
                        
                #         st.success(f"You selected Layout {selected_layout_index + 1} with score: {best_score:.1f}/100")
                    # else:
                    #     # Default to the highest-scoring layout if none selected
                    #     best_layout_index = max(range(len(all_scores)), key=lambda i: all_scores[i][1])
                    #     positions = all_scores[best_layout_index][0]
                    #     placed_objects = [pos[5] for pos in positions]
                    #     best_score = all_scores[best_layout_index][1]
                    #     detailed_scores = all_scores[best_layout_index][2]
                        
                    #     st.session_state.best_layout_score = best_score
                    #     st.session_state.total_score = best_score  # Update the main score variable
                    #     st.session_state.detailed_scores = detailed_scores
            # else:
            #     # Fallback if no good layouts were found
            #     progress_text.text("Optimizing object placement...")
            #     progress_bar.progress(0.7) 

                
            #     # Traditional approach as fallback
            #     positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES, attempt=10000)
            #     placed_objects = [pos[5] for pos in positions]
            #     retry_count = 1
                
            #     while len(placed_objects) < len(selected_objects) and retry_count < 3  :
            #         positions = fit_objects_in_room(bathroom_size, selected_objects, windows_doors, OBJECT_TYPES, attempt=10000)
            #         placed_objects = [pos[5] for pos in positions]
            #         retry_count += 1
            
            # Find available spaces
#             progress_text.text("Analyzing available spaces...")
#             positions = st.session_state.positions
            
#             available_spaces_dict = identify_available_space(positions, (room_width, room_depth), grid_size=1, windows_doors=windows_doors)
            
#             # Mark accessible and inaccessible spaces
#             progress_text.text("Evaluating accessibility...")
#             accessible_spaces, inaccessible_spaces = mark_inaccessible_spaces(
#                 available_spaces_dict['with_shadow'], 
#                 positions, 
#                 (room_width, room_depth), 
#                 windows_doors, 
#                 grid_size=1,
#                 min_path_width=30
#             )
            
#             # Check for non-overlapping spaces
#             non_overlapping_spaces = []
#             for i in range(len(available_spaces_dict['without_shadow'])):
#                 not_overlapping_spaces = []
#                 for j in range(len(available_spaces_dict['without_shadow'])):
#                     if i != j:
#                         overlap = check_overlap(available_spaces_dict['without_shadow'][i], available_spaces_dict['without_shadow'][j])
#                         if not overlap:
#                             not_overlapping_spaces.append(available_spaces_dict['without_shadow'][j])
#                 if len(not_overlapping_spaces) == len(available_spaces_dict['without_shadow'])-1:
#                     non_overlapping_spaces.append(available_spaces_dict['without_shadow'][i])
            
#             # Store results in session state
#             st.session_state.positions = positions
#             st.session_state.bathroom_size = bathroom_size
#             st.session_state.windows_doors = windows_doors
#             st.session_state.available_spaces_dict = available_spaces_dict
#             st.session_state.accessible_spaces = accessible_spaces
#             st.session_state.inaccessible_spaces = inaccessible_spaces
#             st.session_state.non_overlapping_spaces = non_overlapping_spaces
#             st.session_state.generated = True
#             selected_objects = st.session_state.selected_objects
#             bathroom = Bathroom(room_width, room_depth, room_height, positions, windows_doors)
#             layout = Layout(bathroom, selected_objects)
            
#             # Calculate layout score
#             progress_text.text("Evaluating layout quality...")
#             scoring_model = BathroomScoringFunction()
#             total_score, detailed_scores = scoring_model.score(layout)
#             st.session_state.total_score = total_score
#             st.session_state.detailed_scores = detailed_scores
#             # Create visualizations
#             progress_text.text("Creating visualizations...")
#             # Unpack bathroom_size tuple to pass individual width, depth, height parameters
#             bathroom = Bathroom(room_width, room_depth, room_height, positions, windows_doors)
#             # Create 3D visualization
#             visualizer3d = Visualizer3D(bathroom, room_width, room_depth, room_height)
#             fig = visualizer3d.draw_3d_room( positions, windows_doors)
#             st.session_state.fig = fig
            
# # Save 3D figure to bytes for download
#             buf = io.BytesIO()
#             fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
#             buf.seek(0)
#             st.session_state.fig_bytes = buf.getvalue()
#             visualizer2d = Visualizer2D(bathroom)
#             # Create 2D floorplan
#             fig2 = visualizer2d.draw_2d_floorplan()
#             st.session_state.fig2 = fig2
            
#             # Save 2D figure to bytes for download
#             buf2 = io.BytesIO()
#             fig2.savefig(buf2, format='png', dpi=300, bbox_inches='tight')
#             buf2.seek(0)
#             st.session_state.fig2_bytes = buf2.getvalue()
            
#             progress_text.text("Visualizing available spaces...")
#             progress_bar.progress(0.99)  # Use 60% of progress bar for generation
#             figvis_with_shadow = visualizer2d.visualize_available_spaces(positions,  available_spaces_dict['with_shadow'], shadow=True)
#             st.session_state.figvis_with_shadow = figvis_with_shadow
            
#             # Save figure to bytes for download
#             buf3 = io.BytesIO()
#             figvis_with_shadow.savefig(buf3, format='png', dpi=300, bbox_inches='tight')
#             buf3.seek(0)
#             st.session_state.figvis_with_shadow_bytes = buf3.getvalue()
            
#             figvis_without_shadow = visualizer2d.visualize_available_spaces(positions,  available_spaces_dict['without_shadow'], shadow=False)
#             st.session_state.figvis_without_shadow = figvis_without_shadow
            
#             #Save figure to bytes for download
#             buf4 = io.BytesIO()
#             figvis_without_shadow.savefig(buf4, format='png', dpi=300, bbox_inches='tight')
#             buf4.seek(0)
#             st.session_state.figvis_without_shadow_bytes = buf4.getvalue()
            
#             # Calculate space utilization metrics
#             total_room_area = room_width * room_depth
#             used_area = sum(obj[2] * obj[3] for obj in positions)  # width * depth for each object
#             available_area_with_shadow = sum(space[2] * space[3] for space in available_spaces_dict['with_shadow'])
#             available_area_without_shadow = sum(space[2] * space[3] for space in available_spaces_dict['without_shadow'])
            
#             st.session_state.space_metrics = {
#                 "total_room_area": total_room_area,
#                 "used_area": used_area,
#                 "available_area_with_shadow": available_area_with_shadow,
#                 "available_area_without_shadow": available_area_without_shadow
#             }
            
#             # Check if room is valid
#             isTrue = check_valid_room(positions)
#             st.session_state.is_valid_room = isTrue
    
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
                    st.session_state.ml_recommended_layout is not None and
                    st.session_state.rl_recommended_layout is not None and
                    st.session_state.ml_recommended_layout == st.session_state.rl_recommended_layout):
                    # Add 1 to convert from 0-indexed to 1-indexed for display
                    agreed_layout = st.session_state.ml_recommended_layout + 1
                    st.markdown(f"<p style='color: green; font-weight: bold;'>Both Models Recommend Layout: {agreed_layout} ⭐</p>", unsafe_allow_html=True)
                # Get bathroom size and windows/doors from session state
                bathroom_size = st.session_state.bathroom_size
                windows_doors = st.session_state.windows_doors
                
                # Create a container for the layout selection
                layout_selection_container = st.container()
                with layout_selection_container:
                    # Get data from session state
                    all_scores = st.session_state.all_scores
                    layout_metrics = st.session_state.layout_metrics
                    
                    # Get ML and RL recommended layouts if available
                    ml_recommended = st.session_state.ml_recommended_layout if hasattr(st.session_state, 'ml_recommended_layout') else None
                    rl_recommended = st.session_state.rl_recommended_layout if hasattr(st.session_state, 'rl_recommended_layout') else None
                    
                    # Prepare layouts in the format expected by display_layout_selection
                    # layouts = []
                    # for item in all_scores:
                    #     if isinstance(item, tuple) and len(item) >= 3:
                    #         # It's already a tuple with (layout, score, detailed_scores)
                    #         layouts.append(item)
                    #     elif hasattr(item, 'bathroom') and hasattr(item, 'score'):
                    #         # It's a Layout object
                    #         bathroom = item.bathroom if hasattr(item, 'bathroom') else []
                    #         score = item.score if hasattr(item, 'score') else 0
                    #         detailed_scores = item.score_breakdown if hasattr(item, 'score_breakdown') else {}
                    #         layouts.append((bathroom, score, detailed_scores))
                    
                    # Display layouts as 2D floorplans with selection buttons
                    selected_layout_index = display_layout_selection(
                        st.session_state.all_layouts,
                        room_width,
                        room_depth,
                        room_height,
                        windows_doors,
                        layout_metrics=layout_metrics,
                        ml_recommended=ml_recommended,
                        rl_recommended=rl_recommended
                    )
                    
                    # Handle layout selection
                    if selected_layout_index is not None:
                        print(selected_layout_index)
                        layout, score, detailed_scores = st.session_state.all_layouts[selected_layout_index]
                        st.session_state.selected_layout_index = selected_layout_index
                        st.session_state.positions = layout
                        st.session_state.placed_objects = [pos[5] for pos in layout]
                        st.session_state.best_layout_score = score
                        st.session_state.total_score = score
                        st.session_state.detailed_scores = detailed_scores
                        
                        # Add this selection to both models' training data
                        # Train ML model
                        if hasattr(st.session_state, 'ml_model'):
                            try:
                                st.session_state.ml_model.add_training_example(
                                    selected_layout_index, 
                                    st.session_state.all_layouts, 
                                    st.session_state.layout_scores, 
                                    st.session_state.layout_metrics
                                )
                                st.session_state.ml_update_needed = True
                            except Exception as e:
                                st.warning(f"ML model training failed: {e}")
                        
                        # Train RL model
                        if hasattr(st.session_state, 'rl_model'):
                            try:
                                # Extract detailed scores from all_scores
                                # all_scores format: [(layout, score, detailed_scores), ...]
                                detailed_scores_list = [item[2] for item in st.session_state.layout_scores]
                                
                                st.session_state.rl_model.add_training_example(
                                    selected_layout_index, 
                                    st.session_state.all_layouts, 
                                    [item[1] for item in st.session_state.layout_scores],  # Extract scores
                                    detailed_scores_list,
                                    st.session_state.layout_metrics
                                )
                                st.session_state.rl_update_needed = True
                            except Exception as e:
                                st.warning(f"RL model training failed: {e}")
                                st.session_state.rl_update_needed = False
                        
                        # Regenerate visualizations for the selected layout
                        bathroom = Bathroom(room_width, room_depth, room_height, layout, windows_doors)
                        
                        # Create 3D visualization
                        visualizer3d = Visualizer3D(room_width, room_depth, room_height)
                        fig_3d = visualizer3d.draw_3d_room(layout, windows_doors)
                        st.session_state.fig = fig_3d
                        
                        # Save 3D figure to bytes for download
                        buf = io.BytesIO()
                        fig_3d.savefig(buf, format='png', dpi=300, bbox_inches='tight')
                        buf.seek(0)
                        st.session_state.fig_bytes = buf.getvalue()
                        
                        # Create 2D floorplan
                        visualizer2d = Visualizer2D(bathroom)
                        fig_2d = visualizer2d.draw_2d_floorplan()
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
    
                
                # Section 2: Available Spaces Analysis side by side
                st.markdown("<h4 class='section-header'>Available Space Analysis</h4>", unsafe_allow_html=True)
                col0, col1 ,col2,col3 = st.columns([1,2,2,1])
                
                with col1:
                    st.markdown(f"<p><b>With Shadow</b> ({len(st.session_state.available_spaces_dict['with_shadow'])} spaces)</p>", unsafe_allow_html=True)
                    st.pyplot(st.session_state.figvis_with_shadow)
                
                with col2:
                    st.markdown(f"<p><b>Without Shadow</b> ({len(st.session_state.available_spaces_dict['without_shadow'])} spaces)</p>", unsafe_allow_html=True)
                    st.pyplot(st.session_state.figvis_without_shadow)
                
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
                    
                    # Display as a dataframe
                    if object_data:
                        st.dataframe(object_data, use_container_width=True)
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
            
            # # Space utilization metrics
            # st.markdown("<h3 class='section-header'>Space Utilization</h3>", unsafe_allow_html=True)
            
            # metrics = st.session_state.space_metrics
            # total_room_area = metrics["total_room_area"]
            # used_area = metrics["used_area"]
            # available_area_with_shadow = metrics["available_area_with_shadow"]
            # available_area_without_shadow = metrics["available_area_without_shadow"]
            
            
            # # Create a more visual metrics display with 4 columns
            # metric_cols = st.columns([1,2,2,1])
            
            # # Custom metric cards with better alignment
            # with metric_cols[0]:
            #     st.markdown("""
            #     <div class='metric-card'>
            #         <div class='metric-card-label'>Total Room Area</div>
            #         <div class='metric-card-value'>{} cm²</div>
            #     </div>
            #     """.format(total_room_area), unsafe_allow_html=True)
            
            # with metric_cols[1]:
            #     percentage = int(used_area/total_room_area*100)
            #     st.markdown("""
            #     <div class='metric-card'>
            #         <div class='metric-card-label'>Used Area</div>
            #         <div class='metric-card-value'>{} cm²</div>
            #         <div class='metric-card-delta'>{}%</div>
            #     </div>
            #     """.format(used_area, percentage), unsafe_allow_html=True)
            
            # with metric_cols[2]:
            #     percentage = int(available_area_with_shadow/total_room_area*100)
            #     st.markdown("""
            #     <div class='metric-card'>
            #         <div class='metric-card-label'>Available (with shadow)</div>
            #         <div class='metric-card-value'>{} cm²</div>
            #         <div class='metric-card-delta'>{}%</div>
            #     </div>
            #     """.format(available_area_with_shadow, percentage), unsafe_allow_html=True)
            
            # with metric_cols[3]:
            #     percentage = int(available_area_without_shadow/total_room_area*100)
            #     st.markdown("""
            #     <div class='metric-card'>
            #         <div class='metric-card-label'>Available (no shadow)</div>
            #         <div class='metric-card-value'>{} cm²</div>
            #         <div class='metric-card-delta'>{}%</div>
            #     </div>
            #     """.format(available_area_without_shadow, percentage), unsafe_allow_html=True)
            
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
                        import pandas as pd
                        
                        # Total score comparison
                        st.subheader("Total Layout Quality Scores")
                        
                        # Create dataframe for visualization, replacing None values with zeros
                        # Convert None values to 0 for plotting
                        safe_scores = [score if isinstance(score, (int, float)) else 0 for score in layout_scores]
                        
                        df = pd.DataFrame({
                            'Layout': layout_labels,
                            'Score': safe_scores
                        })

                        # Create and display chart
                        fig, ax = plt.subplots(figsize=(10, 4))
                        bars = ax.bar(df['Layout'], df['Score'], color='skyblue')
                        
                        # Only highlight the best score if there are valid scores
                        if any(safe_scores):
                            best_idx = safe_scores.index(max(safe_scores))
                            bars[best_idx].set_color('green')
                        
                        # Add a note if all scores are zero or None
                        if not any(safe_scores):
                            ax.text(0.5, 0.5, 'No valid scores available', 
                                   horizontalalignment='center',
                                   verticalalignment='center',
                                   transform=ax.transAxes,
                                   fontsize=14)
                        
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
                        
                        # Create a dataframe for the metrics table with safe formatting for None values
                        metrics_df = pd.DataFrame({
                            'Layout': layout_labels,
                            'Quality Score': [f"{score:.1f}/100" if isinstance(score, (int, float)) else "N/A" for score in layout_scores],
                            'Objects Placed': [f"{p:.1f}%" if isinstance(p, (int, float)) else "N/A" for p in placed_percentages],
                            'Space Efficiency': [f"{e:.1f}%" if isinstance(e, (int, float)) else "N/A" for e in space_efficiencies]
                        })
                        
                        # Highlight the best row only if there are valid scores
                        safe_scores = [score if isinstance(score, (int, float)) else 0 for score in layout_scores]
                        if any(safe_scores):
                            best_idx = safe_scores.index(max(safe_scores))
                        else:
                            best_idx = 0  # Default to first row if no valid scores
                        
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
            if st.session_state.selected_layout_index is not None:
                st.markdown("<h3 class='section-header'>Layout Quality Score</h3>", unsafe_allow_html=True)
            
            
                total_score = st.session_state.layout_metrics[selected_layout_index]['score']
                # only 3 decimal places
                total_score = round(total_score, 3)
                st.markdown(f"<div style='text-align: left; font-size: 3rem; font-weight: bold; color: {'green' if total_score > 70 else 'orange' if total_score > 40 else 'red'};'>{total_score}/100</div>", unsafe_allow_html=True)
                # Display detailed scores
                detailed_scores = st.session_state.layout_metrics[selected_layout_index]['detailed_scores']
                for category, score in detailed_scores.items():
                    st.markdown(f"**{category}**: {score}/10")


                # Add pathway accessibility analysis
                path_width = 60
                #accessibility_score = st.session_state.detailed_scores["pathway_accessibility"]
                # Analyze pathway accessibility
                # pathway_fig = visualizer2d.visualize_pathway_accessibility(
                #     st.session_state.positions, 

                # )
                
                # Display the accessibility score
                #st.markdown(f"<p>Accessibility Score: <strong>{accessibility_score:.1f}/10</strong></p>", unsafe_allow_html=True)
                
                # Explanation of the score
                #if accessibility_score >= 8:
                #    st.success("Great accessibility! Most fixtures can be reached with comfortable pathways.")
                #elif accessibility_score >= 5:
                #    st.info("Acceptable accessibility. Some fixtures may be difficult to access.")
                #else:
                #    st.warning("Poor accessibility. Consider rearranging fixtures to improve pathways.")
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
                

                if st.session_state.selected_layout_index is not None:
                    total_score = st.session_state.layout_metrics[st.session_state.selected_layout_index]['score']
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
                            room = Bathroom(review.get('room_width'), review.get('room_depth'), review.get('room_height'))
                            room.objects = review.get('objects')
                            room.windows_doors = review.get('windows_doors')
                            visualizer = Visualizer2D(room)
                            img, img_bytes = visualizer.render_saved_floorplan(review)
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
