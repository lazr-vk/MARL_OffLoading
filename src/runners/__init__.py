REGISTRY = {}

from .episode_runner import EpisodeRunner
REGISTRY["episode"] = EpisodeRunner
# from .offloading_runner import OffloadingRunner
from .offloading_test import OffloadingRunner
REGISTRY["offloading"] = OffloadingRunner
from .parallel_runner import ParallelRunner
REGISTRY["parallel"] = ParallelRunner
