

model = DQN(state_dim, action_dim)
model.load_state_dict(torch.load("room_optimizer.pth"))
model.eval()
