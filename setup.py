from setuptools import setup, find_packages

setup(
    name="imfoc",
    version="1.0.2",
    packages=find_packages(),
    install_requires=[
        'PyQt5',
        'Pillow',
        'tqdm',
        'opencv-python',
        'numpy'
    ],
    entry_points={
        'gui_scripts': [
            'imfoc=imfoc:main',
        ],
    },
    package_data={
        'imfoc': ['resources/*.ui', 'resources/*.qm', 'resources/*.ts'],
    },
    include_package_data=True,
)

