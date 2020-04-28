# MLGW
MLGW is a Machine Learning model to compute the gravitational waves generated by a Binary Black Hole coalescence. It is part of a thesis project at Università di Pisa under the supervision of prof. Walter Del Pozzo.
The model is released as a Python package ``mlgw`` in the PyPI repository: <https://pypi.org/project/mlgw/>.
You can install the package with
``pip install mlgw``
The model outputs the waveform when given the two BHs masses and spins. It implements also the dependence of the waveform on the observer position. Basic usage is as follows:
```Python
import mlgw.GW_generator as generator
generator = generator.GW_generator() #creating an istance of the generator
theta = np.array([20,10,0.5,-0.3, 1.43, 1.3, 2.3]) #physical parameters [m1,m2,s1,s2, d_L, iota, phi]
times = np.linspace(-8,0.02, 100000) #time grid at which waves shall be evaluated
h_p, h_c = generator.get_WF(theta, times) #returns amplitude and phase of the wave
```
You can read much more details about the model in the [thesis](https://raw.githubusercontent.com/stefanoschmidt1995/MLGW/master/MLGW_package/docs/thesis.pdf "Thesis").
### Content of the repository
The repository is organised in the following folders:
- **routines**: it holds the core of the project. Every interesting code developed (including also attempts no added to the final release) is kept here.
- **tries**: it stores all the code used to validate the models in routines. The code there is not updated and might not work properly.
- **MLGW_checks**: it holds some test performed on the definitive code, to ensure that there are no bugs.
- **definitive_code**: it holds severeal fitted models as well as a small script to check the accuracy of the models stored.
- **MLGW_package**: it holds code relevant to the package [``mlgw``](https://pypi.org/project/mlgw/ "mlgw package at PyPI").

For more information, you can contact me at [stefanoschmidt1995@gmail.com](mailto:stefanoschmidt1995@gmail.com)

