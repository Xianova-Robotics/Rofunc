import copy
import os

from rofunc.learning.rl.agents.online.a2c_agent import A2CAgent
from rofunc.learning.rl.trainers.base_trainer import BaseTrainer
from rofunc.learning.rl.utils.memory import RandomMemory


class A2CTrainer(BaseTrainer):
    def __init__(self, cfg, env, device):
        super().__init__(cfg, env, device)
        self.memory = RandomMemory(memory_size=cfg.Trainer.rollouts, num_envs=self.env.num_envs, device=device)
        self.agent = A2CAgent(cfg, self.env.observation_space, self.env.action_space, self.memory,
                              device, self.experiment_dir, self.rofunc_logger)

        '''Wandb and Tensorboard'''
        # setup Weights & Biases
        if self.cfg.get("Trainer", {}).get("wandb", False):
            # save experiment config
            trainer_cfg = None  # TODO: check
            trainer_cfg = trainer_cfg if trainer_cfg is not None else {}
            try:
                models_cfg = {k: v.net._modules for (k, v) in self.agent.models.items()}
            except AttributeError:
                models_cfg = {k: v._modules for (k, v) in self.agent.models.items()}
            config = {**self.cfg, **trainer_cfg, **models_cfg}
            # set default values
            wandb_kwargs = copy.deepcopy(self.cfg.get("Trainer", {}).get("wandb_kwargs", {}))
            wandb_kwargs.setdefault("name", os.path.split(self.experiment_dir)[-1])
            wandb_kwargs.setdefault("sync_tensorboard", True)
            wandb_kwargs.setdefault("config", {})
            wandb_kwargs["config"].update(config)
            # init Weights & Biases
            import wandb
            wandb.init(**wandb_kwargs)

    def post_interaction(self):
        self._rollout += 1

        # Update agent
        if not self._rollout % self.rollouts and self._step >= self.start_learning_steps:
            self.agent.update_net()
            self._update_times += 1
            self.rofunc_logger.info(f'Update {self._update_times} times.', local_verbose=False)

        super().post_interaction()