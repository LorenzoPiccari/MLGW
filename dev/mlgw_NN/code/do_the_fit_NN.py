"""
Routine to fit a single NN model, once a PCA dataset is given

A complete model relies on a collection of different modes (e.g. l,m = (2,2), (3,2) etc...).
The fit for each mode relies on the PCA to reduce the dimensionality of the WFs and on several NNs (Neural Networks) to perform a regression from the orbital parameters to the reduced order WF.
The ML models for each mode is stored in a dedicated folder, holding the time grid at which each WF is evaluated, the PCA models for amplitude and phase and the NN models for amplitude and phase. Each NN can be chosen to fit several PC's. Four files are outputted: a figure of training and validation loss as a function of epochs, the weights of the NN models, the features employed for basis function expansion, and the other hyperparameters of the NN with some other general information.
A NN model (in this case for the 22 mode) is thus stored in a folder as follows:
----22
	----lossfunction.png 
	----amp(ph)_PCs.h5 (weights)
	----feat_PCs.txt
	----Model_fit_info.txt

here PCs is a list of (advisedly consecutive) integers structured as [K_1,K_2,...,] where K_i refers to the ith PC.
Function mlgw.fit_model.create_PCA_dataset() and mlgw.fit_model.fit_NN() are helpuf to build such model, once the proper dataset are given

Example usage:
	
	python do_the_fit_NN.py --pca-dataset ../pca_datasets/IMRPhenomTPHM/22 --model-directory ../new_models/test/amp/22 --quantity amp --components 0 1 2 3 4 --max-epoch 100 --units 1 --n-layers 20 --polynomial-order 2 

"""

import argparse
import sys
import os

from mlgw.NN_model import fit_NN, Schedulers, Optimizers, LossFunctions
from mlgw.fit_model import create_PCA_dataset

#########################################################################

parser = argparse.ArgumentParser(__doc__)

parser.add_argument(
	"--pca-dataset", type = str, required = True,
	help="Folder to load the PCA dataset from")

parser.add_argument(
	"--model-directory", type = str, required = True,
	help="Folder where the model files will be stored")

parser.add_argument(
	"--quantity", type = str, required = False, choices = ['amp', 'ph'], default = 'ph',
	help="Wheter to create a model for amplitude of phase")

parser.add_argument(
	"--components", type = int, required = True, nargs = '+',
	help="PCA components to be included in the model")

parser.add_argument(
	"--max-epochs", type = int, required = False, default = 10000,
	help="Maximum number of epochs for the training")

parser.add_argument(
	"--batch-size", type = int, required = False, default = 128,
	help="Batch size for the training")

parser.add_argument(
	"--units", type = int, required = True,
	help="List of units per layer")

parser.add_argument(
	"--n-layers", type = int, required = True,
	help="Number of layers")

parser.add_argument(
	"--polynomial-order", type = int, required = False, default = 1,
	help="Polynomial order for data augmentation features")

parser.add_argument(
	"--learning-rate", type = float, required = False, default = 1e-3,
	help="Learning rate")

parser.add_argument(
	"--activation", type = str, required = False, default = 'sigmoid',
	help="Activation function for each layer")

parser.add_argument(
	"--residual-model", action = 'store_true', required = False, default = False,
	help="Whether the current model is a residual model")


	# Options to create a PCA dataset
parser.add_argument(
	"--waveform-dataset", type = str, required = False,
	help="If given, a PCA dataset will be created from it")

parser.add_argument(
	"--n-comp-amp", type = int, required = False,
	help="Number of components for the PCA amplitude model (only applies if --waveform-dataset is given)")

parser.add_argument(
	"--n-comp-ph", type = int, required = False,
	help="Number of components for the PCA phase model (only applies if --waveform-dataset is given)")

parser.add_argument(
	"--train-frac", type = int, required = False,
	help="Training fraction for the PCA dataset train/validation split (only applies if --waveform-dataset is given)")

args = parser.parse_args()

############################

if args.waveform_dataset:
	if not (args.n_comp_amp and args.n_comp_ph):
		raise ValueError("If a waveform dataset is given, both --n-comp-amp and --n-comp-ph must be provided")
	create_PCA_dataset((args.n_comp_amp, args.n_comp_ph),
		args.waveform_dataset, args.pca_dataset,
		train_frac = 0.8, clean_dataset = False)

#We are assuming the user already has a PCA dataset and that they don't want to create one with this script
#FIXME: add support to create PCA dataset as well. It should be easy enough...


#specify the hyperparameters for the NN
#if a weighted loss function is used, make sure the number of weights equals the number of specified PCs
param_dict = {'layer_list' : [args.units for _ in range(args.n_layers)], #a list with the number of nodes per hidden layer
              'optimizers' : Optimizers("Nadam", args.learning_rate), #the optimizer with (initial) learning rate
              'activation' : args.activation, #activation function between hidden layers (default: sigmoid)
              'batch_size' : args.batch_size, #batch size
              'schedulers' : Schedulers('exponential',exp=-0.0003, min_lr = 1e-4) #how the learning rate decays during training
			 }

features_ = [(['q' ,'s1' ,'s2'], args.polynomial_order)]


#Here we are fitting the NN for the specified quantity (amp or phase) with the specified hyperparameters and features 
print("Saving NN model to: ", args.model_directory)
print("Fitting " + args.quantity)
fit_NN(args.quantity,
	   args.pca_dataset,
	   args.model_directory,
	   hyperparameters = param_dict,
	   N_train = None,
	   comp_to_fit = args.components,
	   features = features_,
	   epochs = args.max_epochs,
	   verbose = True,
	   residual=args.residual_model #IMPORTANT: if you make a residual model, make sure this is set to True. 
)



