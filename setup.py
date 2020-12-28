import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="async_web_scrapper",
    version="0.1.0",
    author="Vadim Makarov",
    author_email="add4che@gmail.com",
    description="Asynchronous abstract web scrapper written in Python with trio",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/run4w4y/async_web_scrapper",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)