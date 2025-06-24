from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="upload-post",
    version="0.1.2",
    author="Manuel Gracia",
    author_email="hi@img2html.com",
    description="Python client for Upload-Post.com API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.upload-post.com/",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.1",
        "python-dotenv>=0.19.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "upload-post=upload_post.cli:main",
        ],
    },
)
