from setuptools import setup
import setuptools
#from distutils.core import setup

import os

with open('README.rst') as f:
    readme = f.read()

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
#print(setuptools.find_packages())
#print(get_list_of_files("mlgw/TD_models"))
#quit()

setup(
    name='mlgw',
    version='3.0.1.post1',
    author='Stefano Schmidt',
    author_email='stefanoschmidt1995@gmail.com',
    packages = setuptools.find_packages(),
#    packages=['mlgw'], 
#    package_dir = {'mlgw':'./mlgw'},
    url="https://github.com/stefanoschmidt1995/MLGW/",
    license='CC by 4.0',
    description='Machine learning modelling of the gravitational waves generated by black-hole binaries',
    long_description=readme,
    include_package_data = True,
    #package_data={'mlgw': get_list_of_files("mlgw/TD_models")},
    package_data={'mlgw': ['TD_models/model_*/*/*', 'TD_models/model_*/README']},
    scripts = ["bin/mlgw_fit_NN", "bin/mlgw_generate_dataset", "bin/mlgw_generate_angle_dataset",
    	"bin/mlgw_tune_NN", "bin/mlgw_write_training_dag"],
    install_requires=[
        "numpy >= 1.16.4",
		"scipy >= 1.2.1",
		"tensorflow >= 2.10.0",
		"keras-tuner >= 1.3.0",
		"precession >= 2.0.0",
		"lalsuite >= 6.62"
    ],
	long_description_content_type = 'text/x-rst',
	command_options={
        'build_sphinx': {
            'source_dir': ('setup.py', 'docs'),
            'build_dir': ('setup.py', 'docs/__build'),
            }},
)





