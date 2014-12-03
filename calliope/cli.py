"""
Copyright (C) 2013 Stefan Pfenninger.
Licensed under the Apache 2.0 License (see LICENSE file).

cli.py
~~~~~~

Command-line interface.

"""

import click
import os
import shutil

from . import core
from . import exceptions
from .parallel import Parallelizer


@click.group()
def cli():
    """Calliope: a multi-scale energy systems (MUSES) modeling framework"""
    pass


@cli.command(short_help='create model')
@click.argument('path')
def new(path):
    """
    Create new model at the given PATH, based on the included example model.
    The directory must not yet exist, and intermediate directories will
    be created automatically.
    """
    # Copies the included example model
    example_model = os.path.join(os.path.dirname(__file__), 'example_model')
    shutil.copytree(example_model, path)
    click.echo('Created new model at: {}'.format(path))


@cli.command(short_help='directly run single model')
@click.argument('run_config')
def run(run_config):
    """Execute the given RUN_CONFIG run configuration file."""
    model = core.Model(config_run=run_config)
    model.config_run.set_key('output.save', True)  # Always save output
    model.run()


@cli.command(short_help='generate parallel runs')
@click.argument('run_config')
@click.argument('path', default='runs')
@click.option('--silent', is_flag=True, default=False,
              help='Be less verbose.')
def generate(run_config, path, silent):
    """
    Generate parallel runs based on the given RUN_CONFIG configuration
    file, saving them in the given PATH, which is a path to a
    directory that must not yet exist (PATH defaults to 'runs'
    if not specified).
    """
    parallelizer = Parallelizer(target_dir=path, config_run=run_config)
    if not silent and 'name' not in parallelizer.config.parallel:
        raise exceptions.ModelError('`' + run_config + '` '
                                    'does not specify a `parallel.name` '
                                    'and was skipped.')
    parallelizer.generate_runs()