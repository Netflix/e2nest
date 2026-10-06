from setuptools import find_packages, setup


setup(
    name="e2nest",
    setup_requires="setupmeta",
    versioning="distance",
    author="Zhi Li (zli@netflix.com), Lukas Krasula (lkrasula@netflix.com)",
    url="https://github.com/Netflix/e2nest",
    package_dir={'': 'nest_site'},
    packages=find_packages(where='nest_site'),
    entry_points={
        'console_scripts': [
            'subjective_study_aom=nest.subjective_study_aom:main',
        ],
    },
)
