from distutils.core import setup

setup(
    name='llvm-xray-tools',
    version='0.0.0',
    packages=['llvm_xray_tools'],
    license='MIT',
    entry_points={
        'console_scripts': [
            'llvm-xray-tools = llvm_xray_tools.__main__:main',
        ],
    },
    install_requires=["argparse", "big_o", "pandas"],
    long_description=open('README.md').read(),
)
