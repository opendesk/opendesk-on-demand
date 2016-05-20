from setuptools import setup, find_packages

setup(
    name = 'opendesk_on_demand',
    version = '0.0.1',
    description = 'Experiments in parameterised customisation of Opendesk products.',
    url = 'https://github.com/opendesk/opendesk-on-demand',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data = True,
    zip_safe = True,
    entry_points = {
        'console_scripts': [
            'compile = opendesk_on_demand.main:main',
        ],
    },
)
