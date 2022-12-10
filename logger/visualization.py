import importlib
from datetime import datetime
from typing import Dict, Any

from utils.util import init_wandb


class TensorboardWriter():
    def __init__(self, log_dir, logger, visual_tool):
        self.writer = None
        self.selected_module = ""
        self.name = "tensorboard"
        if visual_tool != "None":
            log_dir = str(log_dir)

            # Retrieve vizualization writer.
            succeeded = False
            try:
                self.writer = importlib.import_module(visual_tool).SummaryWriter(log_dir)
                succeeded = True
            except ImportError:
                succeeded = False
            self.selected_module = visual_tool

            if not succeeded:
                message = "Warning: visualization (Tensorboard) is configured to use, but currently not installed on " \
                          "this machine. Please install TensorboardX with 'pip install tensorboardx', upgrade PyTorch to " \
                          "version >= 1.1 to use 'torch.utils.tensorboard' or turn off the option in the 'config.json' file."
                logger.warning(message)

        self.step = 0
        self.mode = ''

        self.tb_writer_ftns = {
            'add_scalar', 'add_scalars', 'add_image', 'add_images', 'add_audio',
            'add_text', 'add_histogram', 'add_pr_curve', 'add_embedding'
        }
        self.tag_mode_exceptions = {'add_histogram', 'add_embedding'}
        self.timer = datetime.now()

    def set_step(self, step, mode='train'):
        self.mode = mode
        self.step = step
        if step == 0:
            self.timer = datetime.now()
        else:
            duration = datetime.now() - self.timer
            self.add_scalar('steps_per_sec', 1 / (duration.total_seconds() + 1e6))
            self.timer = datetime.now()

    def __getattr__(self, name):
        """
        If visualization is configured to use:
            return add_data() methods of tensorboard with additional information (step, tag) added.
        Otherwise:
            return a blank function handle that does nothing
        """
        if name in self.tb_writer_ftns:
            add_data = getattr(self.writer, name, None)

            def wrapper(tag, data, *args, **kwargs):
                if add_data is not None:
                    # add mode(train/valid) tag
                    if name not in self.tag_mode_exceptions:
                        tag = '{}/{}'.format(tag, self.mode)
                    add_data(tag, data, self.step, *args, **kwargs)

            return wrapper
        else:
            # default action for returning methods defined in this class, set_step() for instance.
            try:
                attr = object.__getattr__(name)
            except AttributeError:
                raise AttributeError("type object '{}' has no attribute '{}'".format(self.selected_module, name))
            return attr


class Wandb():
    def __init__(self, cfg_trainer, logger, visual_tool, visualize_config=None):
        self.writer = None
        self.selected_module = ""
        self.name = "wandb"
        if visual_tool != "None":
            # Retrieve vizualization writer.
            succeeded = False
            try:
                self.writer = importlib.import_module(visual_tool)
                succeeded = True
            except ImportError:
                succeeded = False
            self.selected_module = visual_tool

            if not succeeded:
                message = "Warning: visualization (Wandb) is configured to use, but currently not installed on this " \
                          "machine. Please install Wandb with 'pip install wandb', set the option in the 'config.json' file."
                logger.warning(message)

        self.writer = init_wandb(self.writer, api_key_file=cfg_trainer['api_key_file'],
                                 project=cfg_trainer['project'], entity=cfg_trainer['entity'],
                                 name=cfg_trainer['name'] if cfg_trainer != "None" else None,
                                 config=visualize_config,
                                 )

        self.step = 0
        self.mode = ''

        self.timer = datetime.now()

    def set_step(self, step, mode='train'):
        self.mode = mode
        self.step = step
        if step == 0:
            self.timer = datetime.now()
        else:
            duration = datetime.now() - self.timer
            self.log({'steps_per_sec': 1 / (duration.total_seconds() + 1e6)})
            self.timer = datetime.now()

    def __getattr__(self, name):
        """
        If visualization is configured to use:
            return add_data() methods of tensorboard with additional information (step, tag) added.
        Otherwise:
            return a blank function handle that does nothing
        """
        add_data = getattr(self.writer, name, None)

        def wrapper(data: Dict[str, Any], *args, **kwargs):
            if add_data is not None:
                # add mode(train/valid) tag
                tag = '{}/{}'.format(list(data.keys())[0], self.mode)
                add_data({tag: list(data.values())[0]}, self.step, *args, **kwargs)

        return wrapper
