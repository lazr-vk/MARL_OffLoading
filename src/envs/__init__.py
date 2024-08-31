from functools import partial
from smac.env import MultiAgentEnv, StarCraft2Env
from .offloadingenv import OffloadingEnv
import sys
import os

def env_fn(env, **kwargs) -> MultiAgentEnv:  # 以key=value的形式传递参数
    return env(**kwargs)

REGISTRY = {}
REGISTRY["sc2"] = partial(env_fn, env=StarCraft2Env)
# REGISTRY["offloading"] = partial(env_fn, env=OffloadingEnv)
REGISTRY["offloading"] = OffloadingEnv

if sys.platform == "linux":
    os.environ.setdefault("SC2PATH",
                          os.path.join(os.getcwd(), "3rdparty", "StarCraftII"))
