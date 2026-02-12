from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="upload-post",
    version="2.0.1",
    author="Upload-Post",
    author_email="hi@img2html.com",
    description="Cross-platform social media upload for TikTok, Instagram, YouTube, LinkedIn, Facebook, Pinterest, Threads, Reddit, Bluesky, and X (Twitter)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.upload-post.com/",
    project_urls={
        "Documentation": "https://docs.upload-post.com",
        "Source": "https://github.com/upload-post/upload-post-pip",
        "Bug Tracker": "https://github.com/upload-post/upload-post-pip/issues",
    },
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.1",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=[
        "social-media", "video-upload", "photo-upload", "tiktok", "instagram",
        "youtube", "linkedin", "facebook", "pinterest", "threads", "reddit",
        "bluesky", "twitter", "x", "api-client", "upload-post"
    ],
    python_requires=">=3.8",
)
