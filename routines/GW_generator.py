"""
Module GW_generator.py
======================
	Definition of class MLGW_generator. The class generates a GW signal of a BBH coalescence when given orbital parameters of the BBH.
	Model performs the regression:
		theta = (q,s1,s2) ---> g ---> A, ph = W g
	First regression is done by a MoE model; the second regression is a PCA model. Some optional parameters can be given to specify the observer position.
	It makes use of modules EM_MoE.py and ML_routines.py for an implementation of a PCA model and a MoE fitted by EM algorithm.
"""
#################

import os
import sys
import warnings
import numpy as np
sys.path.insert(1, os.path.dirname(__file__)) 	#adding to path folder where mlgw package is installed (ugly?)
from EM_MoE import *			#MoE model
from ML_routines import *		#PCA model

################# GW_generator class
class GW_generator(object):
	"""
GW_generator
============
	This class holds all the parts of ML models and acts as GW generator. Model is composed by a PCA model to reduce dimensionality of a WF datasets and by several MoE models to fit PCA in terms of source parameters. WFs can be generated both in time domain and frequency domain.
	Everything is hold in a PCA model (class PCA_model defined in ML_routines) and in two lists of MoE models (class MoE_model defined in EM_MoE). All models are loaded from files in a folder given by user. Files must be named exactly as follows:
		amp(ph)_exp_#		for amplitude (phase) of expert model for PCA component #
		amp(ph)_gat_#		for amplitude (phase) of gating function for PCA component #
		amp(ph)_feat		for list of features to use for MoE models
		amp(ph)_PCA_model	for PCA model for amplitude (phase)
		times/frequencies	file holding grid points at which waves generated by PCA are evaluated
	No suffixes shall be given to files.
	The class doesn't implement methods for fitting: it only provides a useful tool to gather them.
	"""
	def __init__(self, domain, folder = "default"):
		"""
	__init__
	========
		Initialise class by loading models from file and by specifying whether the model works in time domanin (TD) or frequency domain (FD).
		Everything useful for the model must be put within the folder with the standard names:
			{amp(ph)_exp_# ; amp(ph)_gat_#	; amp(ph)_feat ; amp(ph)_PCA_model; times/frequencies}
		There can be an arbitrary number of exp and gating functions as long as they match with each other and they are less than PCA components.
		A compulsory file times/frequencies must hold a list of grid points at which the generated ML wave is evaluated.
		Input:
			domain ("TD"/"FD")	in which domain waves are generated
			folder				address to folder in which everything is kept (if None, models must be loaded manually with load())
		"""
		if domain != "TD" and domain != "FD":
			raise ValueError("Wrong domain chosen ("+domain+")! Allowed domains are \"FD\" and \"TD\"")
		self.domain = domain

		self.frequencies = None #doesn't apply if "TD"
		self.times = None #doesn't apply if "FD"
		
		if folder is not None:
			if folder == "default":
				folder = os.path.dirname(__file__)+"/TD_model"
			self.load(folder)
		return

	def load(self, folder):
		"""
	load
	====
		Builds up all the models from given folder.
		Everything useful for the model must be put within the folder with the standard names:
			{amp(ph)_exp_# ; amp(ph)_gat_#	; amp(ph)_feat ; amp(ph)_PCA_model}
		There can be an arbitrary number of exp and gating functions as long as they match with each other and they are less than PCA components.
		It loads frequencies.
		Input:
			address to folder in which everything is kept
		"""
		if not folder.endswith('/'):
			folder = folder + "/"
		print("Loading model from: ", folder)
		file_list = os.listdir(folder)

			#loading PCA
		self.amp_PCA = PCA_model()
		self.amp_PCA.load_model(folder+"amp_PCA_model")
		self.ph_PCA = PCA_model()
		self.ph_PCA.load_model(folder+"ph_PCA_model")

		print("  Loaded PCA model for amplitude with ", self.amp_PCA.get_V_matrix().shape[1], " PC")
		print("  Loaded PCA model for phase with ", self.ph_PCA.get_V_matrix().shape[1], " PC")

			#loading features
		f = open(folder+"amp_feat", "r")
		self.amp_features = f.readlines()
		for i in range(len(self.amp_features)):
			self.amp_features[i] = self.amp_features[i].rstrip()

		f = open(folder+"ph_feat", "r")
		self.ph_features = f.readlines()
		for i in range(len(self.ph_features)):
			self.ph_features[i] = self.ph_features[i].rstrip()
		
		print("  Loaded features for amplitude: ", self.amp_features)
		print("  Loaded features for phase: ", self.ph_features)
	
			#loading MoE models
		print("  Loading MoE models")
			#amplitude
		self.MoE_models_amp = []
		k = 0
		while "amp_exp_"+str(k) in file_list and  "amp_gat_"+str(k) in file_list:
			self.MoE_models_amp.append(MoE_model(3+len(self.amp_features),1))
			self.MoE_models_amp[-1].load(folder+"amp_exp_"+str(k),folder+"amp_gat_"+str(k))
			print("    Loaded amplitude model for comp: ", k)
			k += 1
		
			#phase
		self.MoE_models_ph = []
		k = 0
		while "ph_exp_"+str(k) in file_list and  "ph_gat_"+str(k) in file_list:
			self.MoE_models_ph.append(MoE_model(3+len(self.ph_features),1))
			self.MoE_models_ph[-1].load(folder+"ph_exp_"+str(k),folder+"ph_gat_"+str(k))
			print("    Loaded phase model for comp: ", k)
			k += 1


		if "frequencies" in file_list and self.domain == "FD":
			self.frequencies = np.loadtxt(folder+"frequencies")
			print("  Loaded frequency vector")
		elif "times" in file_list and self.domain == "TD":
			print("  Loaded time vector")
			self.times = np.loadtxt(folder+"times")
		else:
			raise RuntimeError("Unable to load model: no times/frequency vector given!")

		return

	def MoE_models(self, model_type, k_list=None):
		"""
	MoE_models
	==========
		Returns the MoE model(s).
		Input:
			model_type		"amp" or "ph" to state which MoE models shall be returned
			k_list []		index(indices) of the model to be returned (if None all models are returned)
		Output:
			models []	list of models to be returned
		"""
		if k_list is None:
			k_list = range(self.K)
		if model_type == "amp":
			return self.MoE_models_amp[k]
		if model_type == "ph":
			return self.MoE_models_ph[k]
		return None

	def PCA_models(self, model_type):
		"""
	PCA_models
	==========
		Returns the MoE model(s).
		Input:
			model_type		"amp" or "ph" to state which MoE models shall be returned
		Output:
			
		"""
		if model_type == "amp":
			return self.amp_PCA
		if model_type == "ph":
			return self.ph_PCA
		return None

	def model_summary(self, filename = None):
		"""
	PCA_models
	==========
		Prints to screen a summary of the model currently used.
		If filename is given, output is redirected to file.
		Input:
		Output:
			filename	if not None, redirects the output to file
		"""
		amp_exp_list = [str(model.get_iperparams()[1]) for model in self.MoE_models_amp]
		ph_exp_list = [str(model.get_iperparams()[1]) for model in self.MoE_models_ph]

		output = "###### Summary for MLGW model ######\n"
		output += "   Grid size:     "+str(self.amp_PCA.get_PCA_params()[0].shape[0]) +" \n"
		output += "   Minimum time:  "+str(np.abs(self.times[0]))+" s/M_sun\n"
			#amplitude summary
		output += "   ## Model for Amplitude \n"
		output += "      - #PCs:          "+str(self.amp_PCA.get_PCA_params()[0].shape[1])+"\n"
		output += "      - #Experts:      "+(" ".join(amp_exp_list))+"\n"
		output += "      - #Features:     "+str(self.MoE_models_amp[0].get_iperparams()[0])+"\n"
		output += "      - Features:      "+(" ".join(self.amp_features))+"\n"
			#phase summary
		output += "   ## Model for Phase \n"
		output += "      - #PCs:          "+str(self.ph_PCA.get_PCA_params()[0].shape[1])+"\n"
		output += "      - #Experts:      "+(" ".join(ph_exp_list))+"\n"
		output += "      - #Features:     "+str(self.MoE_models_ph[0].get_iperparams()[0])+"\n"
		output += "      - Features:      "+(" ".join(self.ph_features))+"\n"
		output += "####################################"
	
		if filename is None:
			print(output)
		elif type(filename) is str:
			text_file = open(filename, "a")
			text_file.write(output)
			text_file.close()
		else:
			raise RuntimeError("Filename must be a string! "+str(type(filename))+" given" )
		return
		

	def get_x_grid(self):
		"""
	get_x_grid
	==========
		Returns the grid at which the outputs of the models are evaluated. All grids are in reduced units.
		Output:
			x_grid (D,)	points in frequency grid at which all waves are evaluated
		"""
		if self.domain == "FD":
			return self.frequencies
		if self.domain == "TD":
			return self.times
		return None


	def __call__(self, x_grid, m1, m2, spin1_x, spin1_y, spin1_z, spin2_x, spin2_y, spin2_z, D_L, i, phi_0, long_asc_nodes, eccentricity, mean_per_ano , plus_cross = True):
		"""
	__call__
	========
		Generates a WF according to the MLGW model. It makes all the required preprocessing to include wave dependance on the full 15 parameters space of the GW forms.
		Input:
			x_grid	(N_grid,)		Grid of (physical) time/frequency points to evaluate the wave at
			m1	()/(N,)				Mass of BH 1
			m2	()/(N,)				Mass of BH 1
			spin1_x/y/z	()/(N,)		Each variable represents a spin component of BH 1
			spin2_x/y/z				Each variable represents a spin component of BH 1
			D_L	()/(N,)				Luminosity distance
			i ()/(N,)				Inclination
			phi_0 ()/(N,)			Reference phase for the wave
			long_asc_nodes ()/(N,)	Logitudinal ascentional nodes (currently not implemented)
			eccentricity ()/(N,)	Eccentricity of the orbit (currently not implemented)
			mean_per_ano ()/(N,)	Mean per ano (currently not implemented)
			plus_cross				Whether to return h_+ and h_x components (if false amp and phase are returned)
		Ouput:
			h_plus, h_cross (1,D)/(N,D)	desidered polarizations (if it applies)
			
		"""
		theta = np.column_stack((m1, m2, spin1_x, spin1_y, spin1_z, spin2_x, spin2_y, spin2_z, D_L, i, phi_0, long_asc_nodes, eccentricity, mean_per_ano)) #(N,D)
		return self.get_WF(theta, plus_cross = plus_cross, x_grid= x_grid, red_grid = False)


	def get_WF(self, theta, plus_cross = True, x_grid = None, red_grid = False):
		"""
	get_WF
	======
		Generates a WF according to the MLGW model. It makes all the required preprocessing to include wave dependance on the full 15 parameters space of the GW forms.
		Wherever not specified, all waves are evaluated at a luminosity distance of 1 Mpc.
		It accepts data in one of the following layout of D features:
			D = 3	[q, spin1_z, spin2_z]
			D = 4	[m1, m2, spin1_z, spin2_z]
			D = 5	[m1, m2, spin1_z , spin2_z, D_L]
			D = 6	[m1, m2, spin1_z , spin2_z, D_L, inclination]
			D = 14	[m1, m2, spin1 (3,), spin2 (3,), D_L, inclination, phi_0, long_asc_nodes, eccentricity, mean_per_ano]
		Unit of measures:
			[mass] = M_sun
			[D_L] = Mpc
			[spin] = adimensional
		Input:
			theta (N,D)		source parameters to make prediction at
			plus_cross		whether to return h_+ and h_x components (if false amp and phase are returned)
			x_grid (D',)	a grid in (physical or reduced) time/frequency to evaluate the wave at (uses np.inter)
			red_grid		whether given x_grid is in reduced space (True) or physical space (False)
		Ouput:
			h_plus, h_cross (N,D)	desidered polarizations (if it applies)
			amp,ph (N,D)			desidered amplitude and phase (if it applies)
		"""
		if x_grid is None:
			if self.domain == "FD":
				x_grid = self.frequencies
			if self.domain == "TD":
				x_grid = self.times
				if red_grid == False:
					red_grid = True
					warnings.warn("As no grid is the given, the default reduced grid is used to evaluate the output. red_grid variable is set to True.")

		theta = np.array(theta)
		if theta.ndim == 1:
			theta = theta[np.newaxis,:] #(1,D)
		
		D= theta.shape[1] #number of features given
		if D <3:
			raise RuntimeError("Unable to generata WF. Too few parameters given!!")
			return

			#generating waves
		if self.domain == "TD":
			#res1,res2 = h_plus, h_cross if plus_cross = True
			#res1,res2 = amp, ph if plus_cross = False
			res1, res2 = self.__get_WF_TD__(theta, x_grid, red_grid, plus_cross)
		else:
			amp, ph = self.__get_WF_FD__(theta, x_grid, red_grid, plus_cross)

			#returning to user
		return res1, res2


	def __get_WF_TD__(self, theta, time_grid, red_grid, plus_cross = False):
		"""
	__get_WF_TD__
	=============
		Generates the waves in time domain. Called by get_WF.
		Input:
			theta (N,D)		source parameters to make prediction at
			time_grid (D',)	a grid in (physical or reduced) time to evaluate the wave at (uses np.inter)
			red_grid		whether given x_grid is in reduced space (True) or physical space (False)
		Output:
			amp,ph (N,D)	desidered amplitude and phase
		"""
		D= theta.shape[1] #number of features given
			#setting theta_std & m_tot_us
		if D == 3:
			theta_std = theta
			m_tot_us = 20. * np.ones((theta.shape[0],)) #depending on the convention (ATTENTIOOOOON!!!!!)
		else:
			if D== 14:
				if np.any(np.column_stack((theta[:,2:4], theta[:,5:7])) != 0):
					warnings.warn("Given nonzero spin_x/spin_y components. Model currently supports only spin_z component. Other spin components are ignored")
				s1_id = 4
				s2_id = 7
			else:
				s1_id = 2
				s2_id = 3

			q = np.divide(theta[:,0],theta[:,1]) #mass ratio (general) (N,)
			m_tot_us = theta[:,0] + theta[:,1]	#total mass in solar masses for the user
			theta_std = np.column_stack((q,theta[:,s1_id],theta[:,s2_id])) #(N,3)

			to_switch = np.where(theta_std[:,0] < 1.) #holds the indices of the events to swap

				#switching masses (where relevant)
			theta_std[to_switch,0] = np.power(theta_std[to_switch,0], -1)
			theta_std[to_switch,1], theta_std[to_switch,2] = theta_std[to_switch,2], theta_std[to_switch,1]


		amp, ph =  self.__get_WF__(theta_std) #raw WF (N, N_grid)

			#doing interpolations
		m_tot_std = 20. * np.ones((theta.shape[0],))
			############
		new_amp = np.zeros((amp.shape[0], time_grid.shape[0]))
		new_ph = np.zeros((amp.shape[0], time_grid.shape[0]))
		for i in range(amp.shape[0]):
			if not red_grid:
				interp_grid = time_grid/m_tot_us[i]
			else:
				interp_grid = time_grid
			new_amp[i,:] = np.interp(interp_grid, self.times, amp[i,:]) * m_tot_us[i]/m_tot_std[i]
			new_ph[i,:]  = np.interp(interp_grid, self.times, ph[i,:])
				#setting amplitude to zero if the model extrapolates outiside the grid
			if np.abs(interp_grid[0]) > np.abs(self.times[0]): #try to make it more robust (should work on right as well)
				warnings.warn("Warning: time grid given is too long for the dataset. Results might be subject to errors.")
				indices = np.where(np.abs(interp_grid) > np.abs(self.times[0]))[0]
				new_amp[i,indices] = 0

		amp = 1e-21*new_amp
		ph = new_ph

			#### Dealing with distance and inclination
		dist_pref = np.ones((amp.shape[0],)) #scaling factor for distance (N,)
		cos_i     = np.ones((amp.shape[0],)) # cos(inclination) (N,)

		if D>=5 and D != 14: #distance corrections are done
			dist_pref = theta[:,4] #std_dist = 1 Mpc
		if D == 14:
			dist_pref = theta[:,8] #std_dist = 1 Mpc

		if D>=6 and D != 14: #inclinations corrections are done
			cos_i_sq = np.square(np.cos(theta[:,5])) 
			cos_i = (np.cos(theta[:,5])) #std_inclination = 0.
		if D == 14:
			cos_i_sq = np.square(np.cos(theta[:,9])) 
			cos_i = (np.cos(theta[:,9])) #std_inclination = 0.

			#scaling to required distance
		amp = np.divide(amp.T, dist_pref).T

			#scaling for setting inclination
		if not np.all(cos_i == np.ones((amp.shape[0],))): #dealing with inclination is required (computationally expensive)
			if D == 14:
				phi_0 = theta[:,10]
			else:
				phi_0=0.

			h = amp*np.exp(1j*(ph+phi_0)) #choose here a convention... (+? -?) (lal is +)
			h_p, h_c = h.real, h.imag
			h_p = np.multiply(h_p.T, (1+np.square(cos_i))/2.).T
			h_c = np.multiply(h_c.T, cos_i).T

			if plus_cross:
				return h_p, h_c
			else:
				amp =  np.abs(h_p+1j*h_c) 
				ph = np.unwrap(np.angle(h_p+1j*h_c)) + phi_0
				amp, ph = self.align_wave_TD(amp, ph, time_grid, al_merger = True)
				return amp, ph

		else:
			if plus_cross:
				h = amp*np.exp(1j*(ph+phi_0))
				return h.real, h.imag
			else:
				return amp, ph				

	def __get_WF_FD__(self, theta, freq_grid, red_grid):
		"""
	__get_WF_FD__
	=============
		####Currently doesn't work properly...####
		Generates the waves in time domain. Called by get_WF.
		Input:
			theta (N,D)		source parameters to make prediction at
			time_grid (D',)	a grid in (physical or reduced) time to evaluate the wave at (uses np.inter)
			red_grid		whether given x_grid is in reduced space (True) or physical space (False)
		Output:
			amp,ph (N,D)	desidered amplitude and phase
		"""
			#### Dealing with masses and changing grids
		m_2_train = 10.
		
			#setting theta_std & m_tot
		D= theta.shape[1] #number of features given
		if D == 3:
			theta_std = theta
			m_tot_us = m_2_train*(1+theta_std[:,0]) #total mass in solar masses for the user
		else:
			#here starts the complicated part of scaling things
			q = np.divide(np.max(theta[:,0:2]),np.min(theta[:,0:2])) #mass ratio (N,)

			m_tot_us = theta[:,0] + theta[:,1]	#total mass in solar masses for the user
			if D == 14:
				theta_std = np.column_stack((q,theta[:,4], theta[:,7])) #(N,3)
				if np.any(np.column_stack((theta[:,2:4], theta[:,5:7])) != 0):
					print("Given nonzero spin_x/spin_y components. Model currently supports only spin_z component. Other spin components are ignored")
			else:
				theta_std = np.column_stack((q,theta[:,2:])) #(N,3)

		amp, ph =  self.__get_WF__(theta_std) #(N, N_grid)


		if freq_grid is not None:
			new_amp = np.zeros((amp.shape[0], freq_grid.shape[0]))
			new_ph = np.zeros((ph.shape[0], freq_grid.shape[0]))
			for i in range(amp.shape[0]):
				new_amp[i,:] = np.interp(freq_grid, self.frequencies, amp[i,:])
				new_ph[i,:] = np.interp(freq_grid, self.frequencies, ph[i,:])
			amp = 1e-21*new_amp
			ph = new_ph

		return amp, ph
	
	def get_raw_WF(self,theta):
		"""
	get_raw_WF
	==========
		Returns the wave as generated by the ML model (standard grid and standard m2).
		Input:
			theta (N,3)		source parameters to make prediction at
		Ouput:
			amp,ph (N,D)	desidered amplitude and phase
		"""
		return self.__get_WF__(theta)


	def __get_WF__(self, theta):
		"""
	__get_WF__
	==========
		Generates a WF according to the MLGW model with a parameters vector in MLGW model style (params=  [q,s1z,s2z]).
		All waves are evaluated at a luminosity distance of 1 Mpc and are generated at masses m1 = q * m2 and m2 = 10 M_sun.
		Grid is the standard one.
		Input:
			theta (N,3)		source parameters to make prediction at
		Ouput:
			amp,ph (N,D)	desidered amplitude and phase
		"""
		rec_PCA_dataset_amp, rec_PCA_dataset_ph = self.get_red_coefficients(theta)

		rec_amp_dataset = self.amp_PCA.reconstruct_data(rec_PCA_dataset_amp)
		rec_ph_dataset = self.ph_PCA.reconstruct_data(rec_PCA_dataset_ph)

		return rec_amp_dataset, rec_ph_dataset

	def get_red_coefficients(self, theta):
		"""
	get_red_coefficients
	====================
		Returns the PCA reduced coefficients, as estimated by the MoE models.
		Input:
			theta (N,3)		source parameters to make prediction at
		Ouput:
			red_amp,red_ph (N,K)	PCA reduced amplitude and phase
		"""
		assert theta.shape[1] == 3

			#adding extra features
		amp_theta = add_extra_features(theta, self.amp_features)
		ph_theta = add_extra_features(theta, self.ph_features)

			#making predictions for amplitude
		rec_PCA_dataset_amp = np.zeros((amp_theta.shape[0], self.amp_PCA.get_dimensions()[1]))
		for k in range(len(self.MoE_models_amp)):
			rec_PCA_dataset_amp[:,k] = self.MoE_models_amp[k].predict(amp_theta)

			#making predictions for phase
		rec_PCA_dataset_ph = np.zeros((ph_theta.shape[0], self.ph_PCA.get_dimensions()[1]))
		for k in range(len(self.MoE_models_ph)):
			rec_PCA_dataset_ph[:,k] = self.MoE_models_ph[k].predict(ph_theta)

		return rec_PCA_dataset_amp, rec_PCA_dataset_ph


	def align_wave_TD(self, amp, ph, x_grid = None, al_merger = True, phi_0=0):
		"""
	align_wave_TD
	=============
		Given a set of waves in time domain, it sets time scale s.t. amplitude is max at t=0 (if a grid is given)
		It sets ph = ph_0 at t=0 if al_merger is true; ph=ph_0 at beginning of time grid if al_merger is False.
		Input:
			amp	(N, N_grid)	amplitude of waves
			ph (N,N_grid)	phases of waves
			x_grid (N_grid)	grid at which wave is evaluated	
			phi_0 ()/(N,)	value of phase at the point at which is aligned (default =0)
		Output:
			amp, ph (N,N_grid)	amplitude and phases rescaled appropriately
		"""
		assert amp.shape == ph.shape
		if amp.ndim == 1:
			amp = amp[None,:]
			ph = ph[None,:]

		if x_grid is not None: #adjusting amplitude
			argmax_amp = np.argmax(amp, axis = 1) #(N,)
			#huge_grid = np.linspace(x_grid[0], x_grid[-1], int(1e5))
			for i in range(amp.shape[0]):
				amp[i,:] = np.interp( x_grid, x_grid- x_grid[argmax_amp[i]], amp[i,:])
				ph[i,:]  = np.interp( x_grid, x_grid- x_grid[argmax_amp[i]], ph[i,:])
		
			#aligning phase
		if not al_merger:
			return amp, (np.subtract(ph.T,ph[:,0]) + phi_0).T #this works a lot but is very unelegant!!!

		if al_merger:
			for i in range(amp.shape[0]):
				ph_merger = ph[i,np.argmax(amp[i,:])]
				ph[i,:] = ph[i,:] - ph_merger
			ph = (ph.T + phi_0).T
		return amp, ph

