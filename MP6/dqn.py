import gym
import numpy as np
import torch
from torch import nn
import torch.optim as optim

import utils
from policies import QPolicy


# Modified by Mohit Goyal (mohit@illinois.edu) on 04/20/2022

def make_dqn(statesize, actionsize):
    """
    Create a nn.Module instance for the q leanring model.

    @param statesize: dimension of the input continuous state space.
    @param actionsize: dimension of the descrete action space.

    @return model: nn.Module instance
    """

    class NeuralNet(nn.Module):
        def __init__(self, statesize, actionsize):
            super(NeuralNet, self).__init__()
            self.fc1 = nn.Linear(statesize + 1, statesize + 1, bias=True)
            self.fc2 = nn.Linear(statesize + 1, statesize + 1, bias=True)
            self.fc3 = nn.Linear(statesize + 1, 1, bias=True)

        def forward(self, x):
            x = torch.relu_(self.fc1(x))
            x = torch.relu_(self.fc2(x))
            y = self.fc3(x)
            return y

    return NeuralNet(statesize, actionsize)


class DQNPolicy(QPolicy):
    """
    Function approximation via a deep network
    """

    def __init__(self, model, statesize, actionsize, lr, gamma):
        """
        Inititalize the dqn policy

        @param model: the nn.Module instance returned by make_dqn
        @param statesize: dimension of the input continuous state space.
        @param actionsize: dimension of the descrete action space.
        @param lr: learning rate 
        @param gamma: discount factor
        """
        super().__init__(statesize, actionsize, lr, gamma)
        self.model = model
        self.model.loss_fn = nn.MSELoss()
        self.model.optimizer = optim.SGD(self.model.parameters(self), lr=lr)

    def qvals(self, state):
        """
        Returns the q values for the states.

        @param state: the state
        
        @return qvals: the q values for the state for each action. 
        """
        state = state[0]
        qvals = np.zeros(self.actionsize)
        self.model.eval()
        with torch.no_grad():
            states = torch.from_numpy(state).type(torch.FloatTensor)
            for i in range (actionsize):
                qvals[i] = self.model(np.concatenate(state, np.array(i)))
        return qvals.numpy()

    def td_step(self, state, action, reward, next_state, done):
        """
        One step TD update to the model

        @param state: the current state
        @param action: the action
        @param reward: the reward of taking the action at the current state
        @param next_state: the next state after taking the action at the
            current state
        @param done: true if episode has terminated, false otherwise
        @return loss: total loss the at this time step
        """
        # self.model.train()
        self.model.optimizer.zero_grad()
        sa = np.concatenate((state, action))
        output = self.model.forward(sa)
        max = 0
        for x in range(actionsize):
            candidate = self.model.forward(np.concatenate((state, x)))
            if candidate > max:
                max = candidate
        Q_local = reward + self.gamma * max
        loss = self.model.loss_fn(output, Q_local)
        loss.backward()
        self.model.optimizer.step()

        return loss.item()


    def save(self, outpath):
        """
        saves the model at the specified outpath
        """
        torch.save(self.model, outpath)


if __name__ == '__main__':
    args = utils.hyperparameters()

    env = gym.make('CartPole-v1')
    env.reset(seed=42)  # seed the environment
    np.random.seed(42)  # seed numpy
    import random

    random.seed(42)
    torch.manual_seed(0)  # seed torch
    # torch.use_deterministic_algorithms(True)  # use deterministic algorithms

    statesize = env.observation_space.shape[0]
    actionsize = env.action_space.n

    policy = DQNPolicy(make_dqn(statesize, actionsize), statesize, actionsize, lr=args.lr, gamma=args.gamma)

    utils.qlearn(env, policy, args)

    torch.save(policy.model, 'dqn.model')
