#!/usr/bin/env python


if (__name__ == '__main__'):
    import os
    from zensols.cli import ConfigurationImporterCliHarness
    locs: str = {
        0: 'test-resources/sample.pdf',
        1: 'http://example.com',
        2: 'test-resources/sample.pdf,http://example.com',
        3: f'file://{os.getcwd()}/test-resources/sample.pdf',
        4: f'file://{os.getcwd()}/test-resources/sample.pdf -t url',
        5: 'test-resources/cc.png',
        6: 'test-resources/states.csv',
        7: 'test-resources/renderables/roster-table.json',
        8: 'test-resources/renderables/roster-figure.yml',
    }[8]
    harness = ConfigurationImporterCliHarness(
        src_dir_name='src',
        app_factory_class='zensols.rend.ApplicationFactory',
        proto_args=f'show -H 1200 -W 1200 {locs}',
        proto_factory_kwargs={
            'reload_pattern': r'^zensols\.rend\.?(?!(?:domain|df))\w+'},
    )
    harness.run()
