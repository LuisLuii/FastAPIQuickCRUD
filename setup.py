from setuptools import setup, find_packages

VERSION = '0.0.1-Alpha-10'

print("""

- upload
    - build wheel: python setup.py sdist
    - upload to server: twine upload dist/*

- download
    - Just pip install <package>

""")

if __name__ == '__main__':
    setup(
        name='fastapi_quickcrud',
        version=VERSION,
        install_requires=["fastapi","pydantic","SQLAlchemy==1.4.22","StrEnum","psycopg2","asyncpg"],
        python_requires=">=3.7",
        description="A comprehensive FastaAPI's CRUD router generator for SQLALchemy.",
        long_description=open("README.md").read(),
        long_description_content_type="text/markdown",
        author='Luis Lui',
        author_email='luis11235178@gmail.com',
        url='https://gitlab.com/luislui/quickcrud',
        license="MIT License",
        keywords=["fastapi", "crud", "restful", "routing","SQLAlchemy", "generator", "crudrouter","postgresql","builder"],
        packages=find_packages('src'),
        package_dir={'': 'src'},
        setup_requires=["setuptools>=31.6.0"],
        classifiers=[
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python",
            "Topic :: Internet",
            "Topic :: Software Development :: Libraries :: Application Frameworks",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Software Development :: Libraries",
            "Topic :: Software Development :: Code Generators",
            "Topic :: Software Development",
            "Typing :: Typed",
            "Development Status :: 4 - Beta",
            "Environment :: Web Environment",
            "Framework :: AsyncIO",
            "Intended Audience :: Developers",
            "Intended Audience :: Information Technology",
            "Intended Audience :: System Administrators",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3 :: Only",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
            "Topic :: Internet :: WWW/HTTP",
        ],
        include_package_data=True,
    )
