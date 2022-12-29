import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="exim",
    version="1.0.0",
    author="Hassan Daemshad",
    author_email="daemshad@gmail.com",
    description="stock market exchange simulator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/daemshad/Exim",
    packages=setuptools.find_packages(),
    license="LICENSE",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=["sortedcontainers >= 2", "pandas"],
)
