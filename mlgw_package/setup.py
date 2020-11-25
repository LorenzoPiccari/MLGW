from setuptools import setup
import setuptools
#from distutils.core import setup

import os

def readme():
    with open('README.rst') as f:
        return f.read()

def get_list_of_files(dirName):
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + get_list_of_files(fullPath)
        else:
            allFiles.append(fullPath)
                
    return allFiles


def set_manifest():
    with open('MANIFEST.in', "w") as f:
        f.write("include README.rst\n")
        f.write("include mlgw/TD_models\n")
        data_files = get_list_of_files("mlgw/TD_models") #all files to include
        for data_file in data_files:
            f.write("include "+data_file+"\n")
        f.close()

##################

#set_manifest() #apparently this is done authomatically by setuptools.find_packages()

setup(
    name='mlgw',
    version='2.0.0',
    author='Stefano Schmidt',
    author_email='stefanoschmidt1995@gmail.com',
    packages = setuptools.find_packages(),
#    packages=['mlgw'], 
#    package_dir = {'mlgw':'./mlgw'},
    url="https://github.com/stefanoschmidt1995/MLGW/",
    license='CC by 4.0',
    description='Machine learning modelling of the gravitational waves generated by black-hole binaries',
    long_description=readme(),
    include_package_data = True,
#    package_data={'mlgw': get_list_of_files("mlgw/TD_models")},
    install_requires=[
        "numpy >= 1.16.4",
		"scipy >= 1.2.1",
		#"lalsuite >= 6.62"
    ],
	long_description_content_type = 'text/x-rst'
)





