# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import utils
from . import wizards
from .post_init_hook import post_init_hook as _legacy_post_init_hook


def post_init_hook(env):
    _legacy_post_init_hook(env.cr, env.registry)
