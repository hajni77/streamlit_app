import numpy as np
import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class LayoutPreferenceModel:
    """
    Machine learning model that learns from user layout selections to predict preferred layouts.
    Uses a RandomForest classifier trained on layout features and user selections.
    """
    
    def __init__(self, model_path='layout_preference_model.pkl'):
        """
        Initialize the layout preference model.
        
        Args:
            model_path (str): Path to save/load the trained model
        """
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.training_data = []
        
        # Try to load an existing model if available
        self.load_model()
    
    def extract_features(self, layout, detailed_scores, metrics):
        """
        Extract features from a layout for model training/prediction.
        
        Args:
            layout (list): The layout object positions
            detailed_scores (dict): Detailed scores for the layout
            metrics (dict): Additional metrics like placement percentage and space efficiency
            
        Returns:
            dict: Dictionary of features
        """
        # Basic layout features
        features = {
            'num_objects': len(layout),
            'placed_percentage': metrics.get('placed_percentage', 0),
            'space_efficiency': metrics.get('space_efficiency', 0),
        }
        
        # Add all detailed scores as features
        for score_name, score_value in detailed_scores.items():
            features[f'score_{score_name}'] = score_value
            
        # Extract object-specific features
        object_types = set(obj[5] for obj in layout)
        for obj_type in ['Toilet', 'Sink', 'Double Sink', 'Bathtub', 'Shower']:
            features[f'has_{obj_type.lower().replace(" ", "_")}'] = 1 if obj_type in object_types else 0
            
        # Calculate average distances between objects
        if len(layout) > 1:
            distances = []
            for i, obj1 in enumerate(layout):
                for j, obj2 in enumerate(layout[i+1:], i+1):
                    x1, y1 = obj1[0], obj1[1]
                    x2, y2 = obj2[0], obj2[1]
                    distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    distances.append(distance)
            
            features['avg_object_distance'] = np.mean(distances) if distances else 0
            features['min_object_distance'] = np.min(distances) if distances else 0
            features['max_object_distance'] = np.max(distances) if distances else 0
        else:
            features['avg_object_distance'] = 0
            features['min_object_distance'] = 0
            features['max_object_distance'] = 0
            
        return features
    
    def add_training_example(self, selected_layout_idx, all_layouts,  layout_metrics):
        """
        Add a training example based on user selection.
        
        Args:
            selected_layout_idx (int): Index of the layout selected by the user
            all_layouts (list): List of all generated layouts
            all_scores (list): List of tuples (layout, score, detailed_scores)
            layout_metrics (list): List of dictionaries with layout metrics
        """
        # Extract features for all layouts
        features_list = []
        print(type(all_layouts))
        for i, (layout, score, detailed_scores) in enumerate(all_layouts):
            features = self.extract_features(layout, detailed_scores, layout_metrics[i])
            features['layout_idx'] = i
            features['overall_score'] = score
            features['selected'] = 1 if i == selected_layout_idx else 0
            features_list.append(features)
        
        # Add to training data
        self.training_data.extend(features_list)
        print(f"Added {len(features_list)} training examples, total: {len(self.training_data)}")
        
        # Train the model if we have enough data
        if len(self.training_data) >= 10:  # At least 10 examples
            self.train_model()
    
    def train_model(self):
        """Train the machine learning model on collected data."""
        if not self.training_data:
            print("No training data available")
            return False
        
        # Convert training data to DataFrame
        df = pd.DataFrame(self.training_data)
        
        # Separate features and target
        X = df.drop(['selected', 'layout_idx'], axis=1)
        y = df['selected']
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Split data
        try:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            self.scaler.fit(X_train)
            X_train_scaled = self.scaler.transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"Model trained with accuracy: {accuracy:.2f}")
            
            # Save the model
            self.save_model()
            return True
        except Exception as e:
            print(f"Error training model: {e}")
            return False
    
    def predict_best_layout(self, all_layouts, all_scores, layout_metrics):
        """
        Predict the best layout based on learned preferences.
        
        Args:
            all_layouts (list): List of all generated layouts
            all_scores (list): List of tuples (layout, score, detailed_scores)
            layout_metrics (list): List of dictionaries with layout metrics
            
        Returns:
            int: Index of the predicted best layout
        """
        if self.model is None:
            # If no model is trained yet, return the highest scoring layout
            return max(range(len(all_scores)), key=lambda i: all_scores[i][1])
        
        # Extract features for all layouts
        features_list = []
        for i, (layout, score, detailed_scores) in enumerate(all_scores):
            features = self.extract_features(layout, detailed_scores, layout_metrics[i])
            features_list.append(features)
        
        # Convert to DataFrame with consistent columns
        df = pd.DataFrame(features_list)
        
        # Ensure all expected features are present
        for feature in self.feature_names:
            if feature not in df.columns:
                df[feature] = 0
        
        # Keep only the features the model was trained on
        X = df[self.feature_names]
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Get prediction probabilities
        proba = self.model.predict_proba(X_scaled)
        
        # Get the index with highest probability of being selected
        if proba.shape[1] > 1:  # Check if we have probability for positive class
            best_idx = np.argmax(proba[:, 1])
        else:
            best_idx = 0
            
        return best_idx
    
    def save_model(self):
        """Save the trained model to disk."""
        if self.model is not None:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'training_data': self.training_data
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load a trained model from disk."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data['model']
                    self.scaler = model_data['scaler']
                    self.feature_names = model_data['feature_names']
                    self.training_data = model_data['training_data']
                print(f"Model loaded from {self.model_path}")
                return True
            except Exception as e:
                print(f"Error loading model: {e}")
        return False
    def save_model_to_supabase(self, supabase_client):
        """Save model to Supabase storage using a more reliable approach
        
        Args:
            supabase_client: Initialized Supabase client
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Skip bucket creation - it likely already exists
            # Just serialize and upload the model
            
            # Serialize model to bytes
            model_bytes = pickle.dumps({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'training_data': self.training_data
            })
            
            # Try to update the file if it exists
            try:
                # First check if file exists
                try:
                    files = supabase_client.storage.from_('models').list()
                    file_exists = any(file['name'] == 'layout_preference_model.pkl' for file in files)
                    
                    if file_exists:
                        # Update existing file
                        supabase_client.storage.from_('models').update(
                            'layout_preference_model.pkl',
                            model_bytes,
                            {'content-type': 'application/octet-stream'}
                        )
                        print("Updated existing model file in Supabase storage")
                        return True
                except Exception as e:
                    print(f"Could not check if file exists: {e}")
                    # Continue with upload attempt
                
                # If we get here, either the file doesn't exist or we couldn't check
                # Try a direct upload
                supabase_client.storage.from_('models').upload(
                    'layout_preference_model_2.pkl',
                    model_bytes,
                    {'content-type': 'application/octet-stream'}
                )
                print("Uploaded new model file to Supabase storage")
                return True
                
            except Exception as e:
                if "already exists" in str(e).lower():
                    # Try to remove and then upload
                    try:
                        supabase_client.storage.from_('models').remove(['layout_preference_model.pkl'])
                        print("Removed existing model file")
                        
                        # Now try upload again
                        supabase_client.storage.from_('models').upload(
                            'layout_preference_model.pkl',
                            model_bytes,
                            {'content-type': 'application/octet-stream'}
                        )
                        print("Successfully replaced model in Supabase storage")
                        return True
                    except Exception as remove_error:
                        print(f"Error during remove-then-upload: {remove_error}")
                        return False
                else:
                    print(f"Error during upload: {e}")
                    return False
            
            return True
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
            return False

    def load_model_from_supabase(self, supabase_client):
        """Load model from Supabase storage
        
        Args:
            supabase_client: Initialized Supabase client
            
        Returns:
            bool: True if successful, False otherwise
        """

                
            # Try to get a signed URL for the file (works better with RLS)
        try:
                # Get public URL
                file_url = supabase_client.storage.from_('models').get_public_url('layout_preference_model.pkl')
                print(f"Model file URL: {file_url}")
        except Exception as e:
                print(f"Note: Could not get public URL: {e}")
                # Continue with direct download attempt
            
        # Download from Supabase storage
        response = supabase_client.storage.from_('models').download('layout_preference_model.pkl')
            
        # Deserialize model
        data = pickle.loads(response)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.training_data = data['training_data']
        print("Successfully loaded model from Supabase storage")
        return True

            
    def is_running_on_streamlit_cloud(self):
        """Check if the app is running on Streamlit Cloud or locally
        
        This uses multiple methods to detect the environment:
        1. Check for Streamlit-specific environment variables
        2. Check if we're running in a container (common for cloud deployments)
        3. Look for specific file paths that would indicate cloud deployment
        
        Returns:
            bool: True if running on Streamlit Cloud, False if running locally
        """
        import os
        import socket
        
        # Method 1: Check environment variables that might indicate Streamlit Cloud
        env_vars = ['STREAMLIT_SHARING', 'IS_STREAMLIT_CLOUD', 'STREAMLIT_SERVER_PORT', 'STREAMLIT_SERVER_HEADLESS']
        for var in env_vars:
            if os.environ.get(var) is not None:
                return True
                
        # Method 2: Check if running in a container (common for cloud deployments)
        try:
            with open('/proc/1/cgroup', 'r') as f:
                if 'docker' in f.read() or 'kubepods' in f.read():
                    return True
        except (FileNotFoundError, IOError):
            pass
            
        # Method 3: Check hostname - Streamlit Cloud often uses specific hostname patterns
        hostname = socket.gethostname()
        if 'streamlit' in hostname.lower() or 'heroku' in hostname.lower():
            return True
            
        # Method 4: Create a simple flag file when running locally
        local_flag_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.running_locally')
        if os.path.exists(local_flag_file):
            return False
            
        # If we can't determine for sure, default to assuming it's local
        # You can override this by setting an environment variable
        return os.environ.get('FORCE_CLOUD_STORAGE', '').lower() == 'true'

def get_feature_importance(model):
    """
    Extract feature importance from the model.
    
    Args:
        model (LayoutPreferenceModel): Trained model
        
    Returns:
        dict: Feature importance scores
    """
    if model.model is None or model.feature_names is None:
        return {}
    
    importance = model.model.feature_importances_
    feature_importance = {feature: score for feature, score in zip(model.feature_names, importance)}
    return dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
