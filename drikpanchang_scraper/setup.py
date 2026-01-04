from setuptools import setup, find_packages

setup(
    name='drikpanchang-scraper',
    version='2.0.0',
    description='Navagraha (9-planet) gochar computation using Swiss Ephemeris',
    author='Prakash Kantumutchu',
    packages=find_packages(),
    install_requires=[
        'pandas>=1.5.0',
        'numpy>=1.23.0',
        'python-dateutil>=2.8.2',
        'pytz>=2023.3',
        'pyswisseph>=2.10.0',  # ← KEY DEPENDENCY
        'tqdm>=4.64.0',
    ],
    entry_points={
        'console_scripts': [
            'drikpanchang-scraper=drikpanchang_scraper.cli:main',
        ],
    },
    python_requires='>=3.8',
)
