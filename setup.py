try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

setup(
    name="freelancer_oauth_demo_app",
    author="Freelancer.com",
    author_email="sharding@freelancer.com",
    version="0.2",
    description="Freelancer Demonstration OAuth Application",
    install_requires=[
        "Flask==1.0",
        "Flask-Login==0.3.2",
        "Flask-OAuthlib==0.9.3",
        "oauthlib==1.1.2",  # pin this to 1.1.2 as 2.0.0 is breaking flask oauth
    ],
    dependency_links=[],
    zip_safe=False,
    debian_build_deps=[],
    packages=find_packages(),
    include_package_data=True,
)
