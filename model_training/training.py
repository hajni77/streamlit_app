import torch
from vis import render_environment
import matplotlib.pyplot as plt
from room import RoomEnvironment
from agent import Agent
from dqn import DQN
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Example initial data
objects = [
    [130, 60, 140, 70, 56, "Bathtub", True, True, [0, 0, 0, 0]],
    [0, 0, 50, 60, 85, "Sink", False, True, [60, 0, 0, 0]],
]

type_to_onehot = {
    "Bathtub": [1, 0, 0],
    "Sink": [0, 1, 0],
}

env = RoomEnvironment(objects, type_to_onehot)
state_dim = len(env._get_state())
action_dim = env.num_objects * 4

agent = Agent(state_dim, action_dim, device)

num_episodes = 500
plt.ion()  # Turn on interactive mode for live plotting

for episode in range(num_episodes):
    state = env.reset()
    total_reward = 0
    done = False

    for t in range(200):
        action = agent.select_action(state)
        next_state, reward, done = env.step(action)
        agent.memory.push(state, action, reward, next_state, done)

        state = next_state
        total_reward += reward

        agent.train_step()

        # 👇 Render every N steps
        if t % 100 == 0 or t == 199:
            render_environment(env, episode, t, total_reward)


    print(f"Episode {episode}, Total Reward: {total_reward:.2f}, Epsilon: {agent.epsilon:.2f}")

torch.save(agent.policy_net.state_dict(), "room_optimizer.pth")
