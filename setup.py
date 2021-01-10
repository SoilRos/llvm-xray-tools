from distutils.core import setup

setup(
    name='llvm-xray-tools',
    version='0.0.0',
    packages=['llvm-xray-tools',],
    license='MIT',
    install_requires=["argparse","big_o"],
    long_description=open('README.md').read(),
)