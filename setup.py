import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='PureMusic-TSchluck-ox',
    version='0.0.1',
    author='Tom Schluckbier',
    author_email='tom@schluckbier.com',
    description='Python music writing package',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/TSchluck-ox/PureMusic',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.5',
)
