import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# Streamlit App Title
st.title("Floorplan Review Tool")

door_images = { 
    "front" : "door_front.jpg",
    "left" : "door_left.jpg",
    "right" : "door_right.jpg",
    "back" : "door_back.jpg", 
}


# Layout with Columns
col1, col2 = st.columns([1, 1])  # Create two equal-width columns

with col1:
    # Number Inputs
    x = st.number_input("Enter door distance from the corner (X):", min_value=0, value=0)
    y = st.number_input("E:", min_value=0, value=0)
    width = st.number_input("Enter Width:", min_value=1, value=75)
    height = st.number_input("Enter Height:", min_value=1, value=200)
    
    door = ["Inward", "Outward"]
    selected_room = st.selectbox("Door type:", door)

    # Dropdown Menu for Object Selection
    objects = ["Bathtub", "Sink", "Washing Machine", "Toilet", "Shower","Double Sink", "Cabinet" ]
    selected_object = st.multiselect("Select Objects:", objects)

    # Dropdown Menu for Room Selection
    rooms = [ "Bathroom"]
    selected_room = st.selectbox("Select a Room type:", rooms)

with col2:
    # Display Image Dynamically Based on Selection
    image_path = door_images.get(selected_object, "default.jpg")
    st.image(image_path, caption=f"Selected door position: {selected_object}", use_column_width=True)

# Submit Button
if st.button("Submit"):
    st.success(f"Room: {selected_room}, Object: {selected_object}, Coordinates: ({x}, {y}), Size: {width}x{height}")

# Generate Button for 3D Visualization
if st.button("Generate 3D Plot"):
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')

    # Generate random 3D data (for visualization)
    x_data = np.linspace(x, x + width, 10)
    y_data = np.linspace(y, y + height, 10)
    X, Y = np.meshgrid(x_data, y_data)
    Z = np.sin(X / 10) * np.cos(Y / 10) * 10  # Example function for visualization

    # 3D Surface Plot
    ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='k')

    # Labels and title
    ax.set_xlabel("X Axis")
    ax.set_ylabel("Y Axis")
    ax.set_zlabel("Z Axis")
    ax.set_title(f"3D Visualization of {selected_object} in {selected_room}")

    # Show the plot in Streamlit
    st.pyplot(fig)
