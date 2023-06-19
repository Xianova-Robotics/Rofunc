"""
HumanoidAMP (RofuncRL)
===========================

Humanoid walking, trained by RofuncRL
"""

import argparse
import sys
import isaacgym

from hydra._internal.utils import get_args_parser

from rofunc.config.utils import omegaconf_to_dict, get_config
from rofunc.learning.pre_trained_models.download import model_zoo
from rofunc.learning.RofuncRL.tasks import task_map
from rofunc.learning.RofuncRL.trainers import trainer_map
from rofunc.learning.utils.utils import set_seed


def train(custom_args):
    # Config task and trainer parameters for Isaac Gym environments
    task, motion_file = custom_args.task.split('_')

    sys.argv.append("task={}".format(task))
    sys.argv.append("train={}{}RofuncRL".format(task, custom_args.agent.upper()))
    sys.argv.append("sim_device={}".format(custom_args.sim_device))
    sys.argv.append("rl_device={}".format(custom_args.rl_device))
    sys.argv.append("graphics_device_id={}".format(custom_args.graphics_device_id))
    sys.argv.append("headless={}".format(custom_args.headless))
    sys.argv.append("num_envs={}".format(4096))
    args = get_args_parser().parse_args()
    cfg = get_config('./learning/rl', 'config', args=args)
    cfg.task.env.motion_file = f'amp_humanoid_{motion_file}.npy'
    cfg_dict = omegaconf_to_dict(cfg.task)

    set_seed(cfg.train.Trainer.seed)

    # Instantiate the Isaac Gym environment
    env = task_map[task](cfg=cfg_dict,
                         rl_device=cfg.rl_device,
                         sim_device=cfg.sim_device,
                         graphics_device_id=cfg.graphics_device_id,
                         headless=cfg.headless,
                         virtual_screen_capture=cfg.capture_video,  # TODO: check
                         force_render=cfg.force_render)

    # Instantiate the RL trainer
    trainer = trainer_map[custom_args.agent](cfg=cfg.train,
                                             env=env,
                                             device=cfg.rl_device)

    # Start training
    trainer.train()


def inference(custom_args, ckpt_path=None):
    # Config task and trainer parameters for Isaac Gym environments
    task, motion_file = custom_args.task.split('_')

    sys.argv.append("task={}".format(task))
    sys.argv.append("train={}{}RofuncRL".format(task, custom_args.agent.upper()))
    sys.argv.append("sim_device={}".format(custom_args.sim_device))
    sys.argv.append("rl_device={}".format(custom_args.rl_device))
    sys.argv.append("graphics_device_id={}".format(custom_args.graphics_device_id))
    sys.argv.append("headless={}".format(False))
    sys.argv.append("num_envs={}".format(16))
    args = get_args_parser().parse_args()
    cfg = get_config('./learning/rl', 'config', args=args)
    cfg_dict = omegaconf_to_dict(cfg.task)

    set_seed(cfg.train.Trainer.seed)

    # Instantiate the Isaac Gym environment
    infer_env = task_map[task](cfg=cfg_dict,
                               rl_device=cfg.rl_device,
                               sim_device=cfg.sim_device,
                               graphics_device_id=cfg.graphics_device_id,
                               headless=cfg.headless,
                               virtual_screen_capture=cfg.capture_video,  # TODO: check
                               force_render=cfg.force_render)

    # Instantiate the RL trainer
    trainer = trainer_map[custom_args.agent](cfg=cfg.train,
                                             env=infer_env,
                                             device=cfg.rl_device)
    # load checkpoint
    if ckpt_path is None:
        ckpt_path = model_zoo(name=f"{custom_args.task}.pth")
    trainer.agent.load_ckpt(ckpt_path)

    # Start inference
    trainer.inference()


if __name__ == '__main__':
    gpu_id = 0

    parser = argparse.ArgumentParser()
    # Available tasks: HumanoidAMP_backflip, HumanoidAMP_walk, HumanoidAMP_run, HumanoidAMP_dance, HumanoidAMP_hop
    parser.add_argument("--task", type=str, default="HumanoidAMP_walk")
    parser.add_argument("--agent", type=str, default="amp")  # Available agent: amp
    parser.add_argument("--sim_device", type=str, default="cuda:{}".format(gpu_id))
    parser.add_argument("--rl_device", type=str, default="cuda:{}".format(gpu_id))
    parser.add_argument("--graphics_device_id", type=int, default=gpu_id)
    parser.add_argument("--headless", type=str, default="True")
    parser.add_argument("--inference", action="store_true", help="turn to inference mode while adding this argument")
    parser.add_argument("--ckpt_path", type=str, default=None)
    custom_args = parser.parse_args()

    if not custom_args.inference:
        train(custom_args)
    else:
        inference(custom_args, ckpt_path=custom_args.ckpt_path)
