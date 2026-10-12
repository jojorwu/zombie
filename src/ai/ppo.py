import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
import numpy as np

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class PPOActorCritic(nn.Module):
    """Actor-Critic Neural Network architecture for PPO policy training."""
    def __init__(self, input_dim: int = 57, hidden_dim: int = 64, action_dim: int = 13):
        super(PPOActorCritic, self).__init__()
        self.actor = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Softmax(dim=-1)
        )
        self.critic = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        self.to(DEVICE)

    def forward(self, x: torch.Tensor):
        probs = self.actor(x)
        value = self.critic(x)
        return probs, value

    def get_action(self, obs: np.ndarray):
        state = torch.tensor(obs, dtype=torch.float32, device=DEVICE)
        if state.dim() == 1:
            state = state.unsqueeze(0)
        probs, value = self.forward(state)
        dist = Categorical(probs)
        action = dist.sample()
        return action.item(), dist.log_prob(action), value


class PPOAgent:
    """Proximal Policy Optimization (PPO) agent with Generalized Advantage Estimation (GAE)."""
    def __init__(self, input_dim: int = 57, hidden_dim: int = 64, action_dim: int = 13, lr: float = 3e-4, gamma: float = 0.99, gae_lambda: float = 0.95, clip_eps: float = 0.2):
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_eps = clip_eps
        self.model = PPOActorCritic(input_dim, hidden_dim, action_dim)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.mse_loss = nn.MSELoss()

    def compute_gae(self, rewards, values, masks):
        advantages = []
        gae = 0.0
        val_list = [v.item() if isinstance(v, torch.Tensor) else float(v) for v in values]
        val_ext = val_list + [0.0]
        for t in reversed(range(len(rewards))):
            delta = rewards[t] + self.gamma * val_ext[t + 1] * masks[t] - val_ext[t]
            gae = delta + self.gamma * self.gae_lambda * masks[t] * gae
            advantages.insert(0, gae)
        returns = [adv + val for adv, val in zip(advantages, val_list)]
        return advantages, returns

    def update(self, states, actions, log_probs_old, rewards, masks, values):
        advantages, returns = self.compute_gae(rewards, values, masks)

        returns_t = torch.tensor(returns, dtype=torch.float32, device=DEVICE)
        advantages_t = torch.tensor(advantages, dtype=torch.float32, device=DEVICE)
        states_t = torch.tensor(np.array(states), dtype=torch.float32, device=DEVICE)
        actions_t = torch.tensor(actions, dtype=torch.int64, device=DEVICE)
        old_log_probs_t = torch.tensor(log_probs_old, dtype=torch.float32, device=DEVICE)

        probs, values_pred = self.model(states_t)
        dist = Categorical(probs)
        new_log_probs = dist.log_prob(actions_t)

        ratios = torch.exp(new_log_probs - old_log_probs_t)
        surr1 = ratios * advantages_t
        surr2 = torch.clamp(ratios, 1.0 - self.clip_eps, 1.0 + self.clip_eps) * advantages_t

        actor_loss = -torch.min(surr1, surr2).mean()
        critic_loss = self.mse_loss(values_pred.squeeze(), returns_t)
        loss = actor_loss + 0.5 * critic_loss

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()
