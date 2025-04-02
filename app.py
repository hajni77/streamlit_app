import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# Streamlit App Title
st.title("Object & Room Input Form with 3D Visualization")

# Number Inputs
x = st.number_input("Enter X coordinate:", min_value=0, value=0)
y = st.number_input("Enter Y coordinate:", min_value=0, value=0)
width = st.number_input("Enter Width:", min_value=1, value=50)
height = st.number_input("Enter Height:", min_value=1, value=50)

# Dropdown Menu for Object Selection
objects = ["Car", "Person", "Tree", "Building", "Animal"]
selected_object = st.selectbox("Select an Object:", objects)

# Dropdown Menu for Room Selection
rooms = ["Living Room", "Kitchen", "Bedroom", "Bathroom", "Garage"]
selected_room = st.selectbox("Select a Room:", rooms)

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
