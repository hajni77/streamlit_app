import matplotlib.pyplot as plt
import matplotlib.patches as patches

def render_environment(env, episode=None, step=None, total_reward=None):
    plt.clf()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, 256)
    ax.set_ylim(0, 256)
    ax.set_aspect('equal')
    ax.set_title(f"Episode {episode} Step {step} Reward {total_reward:.2f}")

    colors = ['blue', 'green', 'red', 'purple', 'orange', 'cyan', 'magenta']

    for idx, pos in enumerate(env.positions):
        x, y, width, depth, _, obj_type, movable, visible, shadows = pos
        if not visible:
            continue
        color = colors[idx % len(colors)]
        rect = patches.Rectangle((x, y), width, depth, linewidth=2,
                                  edgecolor=color, facecolor='none')
        ax.add_patch(rect)
        ax.text(x + width/2, y + depth/2, obj_type, ha='center', va='center', color=color, fontsize=8)

    plt.xlim(0, 256)
    plt.ylim(0, 256)
    plt.gca().invert_yaxis()  # Optional: make (0,0) at top-left like many UI editors
    plt.pause(3)
    plt.close()