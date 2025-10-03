# 3D Bathroom Layout Generator

A Streamlit-based web application for designing and visualizing bathroom layouts in 3D and 2D. The app uses algorithms to automatically place fixtures (toilets, sinks, bathtubs, etc.) in optimal positions based on room dimensions, design constraints, and best practices.

---

## Features
- **Intuitive Streamlit interface** for specifying room size and selecting fixtures
- **Automated fixture placement** with optimization for usability and aesthetics
- **3D and 2D visualization** powered by Matplotlib
- **Authentication** and data storage via Supabase
- **Review submission** and feedback collection
- **Extensible architecture** for adding new fixture types and optimization strategies

---

## Project Structure

- `app.py` — Main Streamlit app and UI logic
- `generate_room.py` — Core placement and constraint algorithms
- `optimization.py` — Space utilization and layout optimization
- `visualization.py` — 3D/2D rendering and shadow visualization
- `utils.py` — Geometry, sizing, and validation utilities
- `object_types.json` — Fixture specs, constraints, and placement priorities
- `authentication.py` — User authentication and session handling
- `.streamlit/` — Streamlit configuration and secrets
- `requirements.txt` — Python dependencies
- `PLANNING.md` — Architecture, design principles, and style guide
- `TASK.md` — Task tracking, future enhancements, and known issues

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd streamlit_app
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Supabase credentials:**
   - Add your Supabase keys to `.streamlit/secrets.toml` as described in the [Supabase docs](https://supabase.com/docs/guides/api/)

4. **Run the app:**
   ```bash
   streamlit run app.py
   ```

---

## Usage
1. Enter room dimensions and select fixtures
2. Generate layout and review the 3D/2D visualizations
3. Adjust fixture positions if needed (future feature)
4. Save or export your design
5. Submit feedback to improve the app

---

## Roadmap & Future Enhancements
- Machine learning for layout optimization
- AR/VR and mobile visualization
- Integration with product catalogs and cost estimation
- Plumbing, electrical, and lighting simulation
- Accessibility and code compliance checking

See `TASK.md` and `PLANNING.md` for the full roadmap, technical constraints, and design principles.

---

## License
MIT License. See `LICENSE` file for details.

---

## Acknowledgements
- Built with [Streamlit](https://streamlit.io/), [Matplotlib](https://matplotlib.org/), and [Supabase](https://supabase.com/)
- Inspired by best practices in bathroom design and architectural planning
