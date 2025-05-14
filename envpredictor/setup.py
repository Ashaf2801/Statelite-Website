from setuptools import setup, find_packages

setup(
    name='envpredictor',
    version='0.1.0',
    description='High-accuracy environmental prediction using TensorFlow models',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=[
        'tensorflow>=2.10.0',
        'numpy>=1.23.0',
        'python-dateutil>=2.8.2'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)