import numpy as np
import pandas as pd
import pickle
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
import random
from collections import deque

class BathroomLayoutEnvironment:
    """
    Environment for bathroom layout optimization using reinforcement learning.
    This environment represents the state of bathroom layouts and provides
    methods for the agent to interact with them.
    """
    
    def __init__(self, layouts, scores, detailed_scores, layout_metrics):
        """
        Initialize the bathroom layout environment.
        
        Args:
            layouts (list): List of bathroom layouts
            scores (list): List of overall scores for each layout
            detailed_scores (list): List of detailed scores for each layout
            layout_metrics (list): List of metrics for each layout
        """
        self.layouts = layouts
        self.scores = scores
        self.detailed_scores = detailed_scores
        self.layout_metrics = layout_metrics
        self.current_layout_idx = 0
        self.history = []
        
    def reset(self):
        """
        Reset the environment to initial state.
        
        Returns:
            numpy.ndarray: The initial state representation
        """
        self.current_layout_idx = 0
        self.history = []
        return self._get_state()
    
    def step(self, action):
        """
        Take an action in the environment.
        
        Args:
            action (int): Index of the layout to select (0-9)
            
        Returns:
            tuple: (next_state, reward, done, info)
        """
        # Record the action in history
        self.history.append(action)
        
        # Calculate reward based on the selected layout's score
        reward = self.scores[action]
        
        # Move to the next layout
        self.current_layout_idx = action
        
        # Check if we're done (for now, we're done after each selection)
        done = True
        
        # Return the next state, reward, done flag, and info
        return self._get_state(), reward, done, {"layout_idx": action}
    
    def _get_state(self):
        """
        Get the current state representation.
        
        Returns:
            numpy.ndarray: The state representation
        """
        # Create a feature vector for each layout
        features = []
        
        for i in range(len(self.layouts)):
            layout = self.layouts[i]
            detailed_score = self.detailed_scores[i]
            metrics = self.layout_metrics[i]
            
            # Extract basic layout features
            layout_features = [
                len(layout),  # Number of objects
                metrics.get('placed_percentage', 0),
                metrics.get('space_efficiency', 0),
            ]
            
            # Add detailed scores
            for score_name, score_value in detailed_score.items():
                layout_features.append(score_value)
                
            # Count object types
            object_types = {'toilet': 0, 'sink': 0, 'double_sink': 0, 'bathtub': 0, 'shower': 0}
            for obj in layout:
                obj_type = obj[5].lower()
                if obj_type in object_types:
                    object_types[obj_type] += 1
                    
            # Add object counts to features
            layout_features.extend(list(object_types.values()))
            
            # Calculate distances between objects if there are multiple objects
            if len(layout) > 1:
                distances = []
                for i, obj1 in enumerate(layout):
                    for j, obj2 in enumerate(layout[i+1:], i+1):
                        x1, y1 = obj1[0], obj1[1]
                        x2, y2 = obj2[0], obj2[1]
                        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                        distances.append(distance)
                
                layout_features.append(np.mean(distances) if distances else 0)
                layout_features.append(np.min(distances) if distances else 0)
                layout_features.append(np.max(distances) if distances else 0)
            else:
                layout_features.extend([0, 0, 0])  # No distances if only one object
                
            features.append(layout_features)
            
        return np.array(features, dtype=np.float32)


class PolicyNetwork(nn.Module):
    """
    Neural network for the policy (actor) in the actor-critic architecture.
    """
    
    def __init__(self, input_dim, hidden_dim, output_dim):
        """
        Initialize the policy network.
        
        Args:
            input_dim (int): Dimension of input features
            hidden_dim (int): Dimension of hidden layer
            output_dim (int): Dimension of output (number of actions)
        """
        super(PolicyNetwork, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, x):
        """
        Forward pass through the network.
        
        Args:
            x (torch.Tensor): Input tensor
            
        Returns:
            torch.Tensor: Output tensor
        """
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return torch.softmax(x, dim=-1)


class ValueNetwork(nn.Module):
    """
    Neural network for the value function (critic) in the actor-critic architecture.
    """
    
    def __init__(self, input_dim, hidden_dim):
        """
        Initialize the value network.
        
        Args:
            input_dim (int): Dimension of input features
            hidden_dim (int): Dimension of hidden layer
        """
        super(ValueNetwork, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 1)
        
    def forward(self, x):
        """
        Forward pass through the network.
        
        Args:
            x (torch.Tensor): Input tensor
            
        Returns:
            torch.Tensor: Output tensor
        """
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x


class LayoutRLModel:
    """
    Reinforcement learning model for bathroom layout optimization.
    Uses an actor-critic architecture to learn from user selections.
    """
    
    def __init__(self, model_path='.layout_rl_model.pkl', feature_dim=28, hidden_dim=128, num_layouts=10):
        """
        Initialize the layout RL model.
        
        Args:
            model_path (str): Path to save/load the trained model
            feature_dim (int): Initial dimension of features for each layout (will adapt dynamically)
            hidden_dim (int): Dimension of hidden layers in networks
            num_layouts (int): Number of layouts to choose from (default: 10)
        """
        self.model_path = model_path
        self.feature_dim = feature_dim  # This will be updated dynamically if needed
        self.hidden_dim = hidden_dim
        self.num_layouts = num_layouts
        self.model_initialized = False
        
        # Set model attribute for compatibility with app.py
        self.model = True
        
        # Initialize networks and optimizer lazily when we know the feature dimensions
        self.policy_net = None
        self.value_net = None
        self.policy_optimizer = None
        self.value_optimizer = None
        
        # Try to load model if exists
        self.load_model()
        
    def _initialize_networks(self, feature_dim=None):
        """
        Initialize or reinitialize the networks with the given feature dimension.
        
        Args:
            feature_dim (int, optional): Feature dimension to use. If None, use self.feature_dim.
        """
        if feature_dim is not None:
            self.feature_dim = feature_dim
            
        # Initialize actor and critic networks
        self.policy_net = PolicyNetwork(self.feature_dim, self.hidden_dim, self.num_layouts)
        self.value_net = ValueNetwork(self.feature_dim, self.hidden_dim)
        
        # Initialize optimizer
        self.policy_optimizer = optim.Adam(self.policy_net.parameters(), lr=0.001)
        self.value_optimizer = optim.Adam(self.value_net.parameters(), lr=0.001)
        
        # Experience replay buffer
        self.memory = deque(maxlen=10000)
        
        # Hyperparameters
        self.gamma = 0.99  # Discount factor
        self.eps = 1e-8  # Small epsilon for numerical stability
        
        self.model_initialized = True
    
    def select_action(self, state):
        """
        Select an action (layout) based on the current policy.
        
        Args:
            state (numpy.ndarray): Current state representation
            
        Returns:
            int: Selected layout index
        """
        state = torch.FloatTensor(state)
        probs = self.policy_net(state)
        m = Categorical(probs)
        action = m.sample()
        return action.item(), m.log_prob(action)
    
    def predict_best_layout(self, layouts, scores, detailed_scores, layout_metrics):
        """
        Predict the best layout based on learned policy.
        
        Args:
            layouts (list): List of bathroom layouts
            scores (list): List of overall scores for each layout
            detailed_scores (list): List of detailed scores for each layout
            layout_metrics (list): List of metrics for each layout
            
        Returns:
            int: Index of the predicted best layout
        """
        try:
            # Create environment
            env = BathroomLayoutEnvironment(layouts, scores, detailed_scores, layout_metrics)
            
            # Get state
            state = env.reset()
            
            # Check if networks are initialized
            if not self.model_initialized:
                actual_feature_dim = state.shape[1]
                print(f"Initializing networks with feature dimension: {actual_feature_dim}")
                self._initialize_networks(actual_feature_dim)
            
            # Check if feature dimensions match
            actual_feature_dim = state.shape[1]
            if actual_feature_dim != self.feature_dim:
                print(f"Recreating policy network to match feature dimensions: {actual_feature_dim}")
                # Recreate the policy network with the correct feature dimensions
                self._initialize_networks(actual_feature_dim)
                
                # If we have a saved model, we can't use it with different dimensions
                # So we'll fall back to a simple heuristic
                print("Using score-based heuristic for layout selection")
                return scores.index(max(scores))
            
            # Get action probabilities
            state_tensor = torch.FloatTensor(state)
            with torch.no_grad():
                probs = self.policy_net(state_tensor)
            
            # Return the layout with highest probability
            return torch.argmax(probs).item()
        except Exception as e:
            print(f"Error in predict_best_layout: {e}")
            # Fall back to selecting the highest scoring layout
            return scores.index(max(scores))
    
    def add_training_example(self, selected_layout_idx, layouts, scores, detailed_scores, layout_metrics):
        """
        Add a training example based on user selection.
        
        Args:
            selected_layout_idx (int): Index of the layout selected by the user
            layouts (list): List of bathroom layouts
            scores (list): List of overall scores for each layout
            detailed_scores (list): List of detailed scores for each layout
            layout_metrics (list): List of metrics for each layout
        """
        # Create environment
        env = BathroomLayoutEnvironment(layouts, scores, detailed_scores, layout_metrics)
        
        # Get state
        state = env.reset()
        
        # Take the selected action
        next_state, reward, done, _ = env.step(selected_layout_idx)
        
        # Store the experience in memory
        self.memory.append((state, selected_layout_idx, reward, next_state, done))
        
        # Train the model if we have enough examples
        if len(self.memory) >= 10:
            self.train_model()
    
    def train_model(self, batch_size=32, epochs=10):
        """
        Train the model on collected experiences.
        
        Args:
            batch_size (int): Number of experiences to sample for each update
            epochs (int): Number of training epochs
        """
        if len(self.memory) < batch_size:
            print(f"Not enough training examples. Have {len(self.memory)}, need {batch_size}.")
            return
        
        for _ in range(epochs):
            # Sample a batch of experiences
            if len(self.memory) < batch_size:
                batch = list(self.memory)
            else:
                batch = random.sample(self.memory, batch_size)
            
            states, actions, rewards, next_states, dones = zip(*batch)
            
            # Convert to tensors
            states = torch.FloatTensor(np.vstack(states))
            actions = torch.LongTensor(actions)
            rewards = torch.FloatTensor(rewards)
            next_states = torch.FloatTensor(np.vstack(next_states))
            dones = torch.FloatTensor(dones)
            
            # Calculate advantages
            with torch.no_grad():
                next_values = self.value_net(next_states).squeeze()
                targets = rewards + self.gamma * next_values * (1 - dones)
            
            values = self.value_net(states).squeeze()
            advantages = targets - values
            
            # Update value network
            value_loss = nn.MSELoss()(values, targets)
            self.value_optimizer.zero_grad()
            value_loss.backward()
            self.value_optimizer.step()
            
            # Update policy network
            probs = self.policy_net(states)
            m = Categorical(probs)
            log_probs = m.log_prob(actions)
            policy_loss = -(log_probs * advantages.detach()).mean()
            
            self.policy_optimizer.zero_grad()
            policy_loss.backward()
            self.policy_optimizer.step()
            
        print(f"Model trained on {len(self.memory)} examples.")
        self.save_model()
    
    def save_model(self):
        """
        Save the trained model to disk.
        """
        try:
            model_data = {
                'policy_state_dict': self.policy_net.state_dict(),
                'value_state_dict': self.value_net.state_dict(),
                'feature_dim': self.feature_dim,
                'hidden_dim': self.hidden_dim,
                'num_layouts': self.num_layouts
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            # Set model attribute to indicate model is available
            self.model = model_data
            print(f"Model saved to {self.model_path}")
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self):
        """
        Load a trained model from disk.
        
        Returns:
            bool: True if model was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                # Get dimensions from saved model
                saved_feature_dim = model_data['feature_dim']
                saved_hidden_dim = model_data['hidden_dim']
                saved_num_layouts = model_data['num_layouts']
                
                print(f"Loading model with feature dimension: {saved_feature_dim}")
                
                # Update instance variables
                self.feature_dim = saved_feature_dim
                self.hidden_dim = saved_hidden_dim
                self.num_layouts = saved_num_layouts
                
                # Initialize networks with loaded dimensions
                self.policy_net = PolicyNetwork(self.feature_dim, self.hidden_dim, self.num_layouts)
                self.value_net = ValueNetwork(self.feature_dim, self.hidden_dim)
                
                # Initialize optimizers
                self.policy_optimizer = optim.Adam(self.policy_net.parameters(), lr=0.001)
                self.value_optimizer = optim.Adam(self.value_net.parameters(), lr=0.001)
                
                # Experience replay buffer
                self.memory = deque(maxlen=10000)
                
                # Hyperparameters
                self.gamma = 0.99  # Discount factor
                self.eps = 1e-8  # Small epsilon for numerical stability
                
                # Load state dictionaries
                self.policy_net.load_state_dict(model_data['policy_state_dict'])
                self.value_net.load_state_dict(model_data['value_state_dict'])
                
                # Recreate optimizers
                self.policy_optimizer = optim.Adam(self.policy_net.parameters(), lr=0.001)
                self.value_optimizer = optim.Adam(self.value_net.parameters(), lr=0.001)
                
                # Set model attribute to indicate model is available
                self.model = model_data
                
                print(f"Model loaded from {self.model_path}")
                return True
            else:
                print(f"No model found at {self.model_path}")
                self.model = None
                return False
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
            return False
    
    def save_model_to_supabase(self, supabase_client):
        """
        Save model to Supabase storage.
        
        Args:
            supabase_client: Initialized Supabase client
            user_id: Optional user ID for user-specific storage
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First save the model locally
            self.save_model()
            
            # Serialize model to bytes
            model_bytes = pickle.dumps({
                'policy_state_dict': self.policy_net.state_dict(),
                'value_state_dict': self.value_net.state_dict(),
                'feature_dim': self.feature_dim,
                'hidden_dim': self.hidden_dim,
                'num_layouts': self.num_layouts
            })
            
            # Determine file name - use user-specific file if user_id is provided
            file_name = f"layout_preference_model_rl.pkl"
            print(f"Saving model as {file_name}")
            
            # Try to update the file if it exists
            try:
                # First check if file exists
                try:
                    files = supabase_client.storage.from_('models').list()
                    file_exists = any(file['name'] == file_name for file in files)
                    
                    if file_exists:
                        # Update existing file
                        supabase_client.storage.from_('models').update(
                            file_name,
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
                    file_name,
                    model_bytes,
                    {'content-type': 'application/octet-stream'}
                )
                print("Uploaded new model file to Supabase storage")
                return True
                
            except Exception as e:
                if "already exists" in str(e).lower():
                    # Try to remove and then upload
                    try:
                        supabase_client.storage.from_('models').remove([file_name])
                        print("Removed existing model file")
                        
                        # Now try upload again
                        supabase_client.storage.from_('models').upload(
                            file_name,
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
        except Exception as e:
            print(f"Error saving model to Supabase: {e}")
            return False
            
    def load_model_from_supabase(self, supabase_client):
        """Load model from Supabase storage
        
        Args:
            supabase_client: Initialized Supabase client
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First check if the bucket exists
            try:
                buckets = supabase_client.storage.list_buckets()
                bucket_exists = False
                for bucket in buckets:
                    if bucket['name'] == 'models':
                        bucket_exists = True
                        break
                        
                if not bucket_exists:
                    print("'models' bucket doesn't exist in Supabase storage")
                    return False
            except Exception as e:
                print(f"Warning: Bucket check failed: {e}")
                # Continue anyway, the download might still work
                
            # Try to get a signed URL for the file (works better with RLS)
            try:
                # Get public URL
                file_url = supabase_client.storage.from_('models').get_public_url('layout_preference_model_rl.pkl')
                print(f"Model file URL: {file_url}")
            except Exception as e:
                print(f"Note: Could not get public URL: {e}")
                # Continue with direct download attempt
            
            # Download from Supabase storage
            response = supabase_client.storage.from_('models').download('layout_preference_model_rl.pkl')
            
            # Deserialize model
            data = pickle.loads(response)
            self.model = data['model']
            self.scaler = data['scaler']
            self.feature_names = data['feature_names']
            self.training_data = data['training_data']
            print("Successfully loaded model from Supabase storage")
            return True
        except Exception as e:
            print(f"Error loading model from Supabase: {e}")
            return False
    
    def is_running_on_streamlit_cloud(self):
        """
        Check if the app is running on Streamlit Cloud or locally.
        
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
        return os.environ.get('FORCE_CLOUD_STORAGE', '').lower() == 'true'


def get_feature_importance(model):
    """
    Extract feature importance from the RL model.
    
    Args:
        model (LayoutRLModel): Trained model
        
    Returns:
        dict: Feature importance scores based on policy network weights
    """
    if not hasattr(model, 'policy_net'):
        return {}
    
    # Get weights from the first layer of the policy network
    weights = model.policy_net.fc1.weight.data.abs().mean(dim=0).numpy()
    
    # Define feature names (must match the features extracted in BathroomLayoutEnvironment._get_state)
    feature_names = [
        'num_objects',
        'placed_percentage',
        'space_efficiency',
        'score_accessibility',
        'score_aesthetics',
        'score_functionality',
        'score_spacing',
        'count_toilet',
        'count_sink',
        'count_double_sink',
        'count_bathtub',
        'count_shower',
        'avg_object_distance',
        'min_object_distance',
        'max_object_distance'
    ]
    
    # Ensure we have the right number of feature names
    if len(feature_names) < len(weights):
        # Add generic names for any additional features
        for i in range(len(feature_names), len(weights)):
            feature_names.append(f'feature_{i}')
    elif len(feature_names) > len(weights):
        # Truncate feature names if we have too many
        feature_names = feature_names[:len(weights)]
    
    # Create a dictionary of feature importances
    feature_importance = {name: float(weight) for name, weight in zip(feature_names, weights)}
    
    # Sort by importance
    return dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
