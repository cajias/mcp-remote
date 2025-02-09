from setuptools import setup, find_packages

setup(
    name='mpc-remote',
    version='0.1.0',
    description='ZeroMQ implementation of the Model Context Protocol',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='MPC Remote Contributors',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.8',
    install_requires=[
        'pyzmq>=25.1.2',
        'jsonschema>=4.0.0',
        'cryptography>=3.4.0'
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.1.0',
            'ruff>=0.3.5'
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    license='MIT'
)