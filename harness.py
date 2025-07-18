#!/usr/bin/env python

import os
from zensols.cli import ConfigurationImporterCliHarness

if (__name__ == '__main__'):
    locs: str = {
        0: 'test-resources/sample.pdf',
        1: 'http://example.com',
        2: 'test-resources/sample.pdf,http://example.com',
        3: f'file://{os.getcwd()}/test-resources/sample.pdf',
        4: f'file://{os.getcwd()}/test-resources/sample.pdf -t url',
        5: 'test-resources/states.csv',
    }[5]
    harness = ConfigurationImporterCliHarness(
        src_dir_name='src',
        app_factory_class='zensols.rend.ApplicationFactory',
        proto_args=f'show -H 1200 -W 1200 {locs}',
        proto_factory_kwargs={
            'reload_pattern': r'^zensols\.rend\.?(?!domain)'},
    )
    harness.run()
