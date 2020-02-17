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
	def __init__(self, folder = "default"):
		"""
	__init__
	========
		Initialise class by loading models from file. "default" loads a pre-fitted default model (saved in "__dir__/TD_model").
		Everything useful for the model must be put within the folder with the standard names:
			{amp(ph)_exp_# ; amp(ph)_gat_#	; amp(ph)_feat ; amp(ph)_PCA_model; times/frequencies}
		There can be an arbitrary number of exp and gating functions as long as they match with each other and they are less than PCA components.
		A compulsory file times/frequencies must hold a list of grid points at which the generated ML wave is evaluated.
		Input:
			folder				address to folder in which everything is kept (if None, models must be loaded manually with load())
		"""
		self.times = None
		
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

		if "times" in file_list:
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
	
		if type(filename) is str:
			text_file = open(filename, "a")
			text_file.write(output)
			text_file.close()
			return
		elif filename is not None:
			warnings.warn("Filename must be a string! "+str(type(filename))+" given. Output is redirected to standard output." )
		print(output)
		return

	def get_time_grid(self):
		"""
	get_time_grid
	=============
		Returns the time grid at which the outputs of the models are evaluated. Grid is in reduced units.
		Output:
			time_grid (D,)	points in time grid at which all waves are evaluated
		"""
		return self.times


	def __call__(self, x_grid, m1, m2, spin1_x, spin1_y, spin1_z, spin2_x, spin2_y, spin2_z, D_L, i, phi_0, long_asc_nodes, eccentricity, mean_per_ano , plus_cross = True):
		"""
	__call__
	========
		Generates a WF according to the MLGW model. It makes all the required preprocessing to include wave dependance on the full 14 parameters space of the GW forms.
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
			amp, phase (1,D)/(N,D)		desidered amplitude and phase (if it applies)
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
			D = 7	[m1, m2, spin1_z , spin2_z, D_L, inclination, phi_0]
			D = 14	[m1, m2, spin1 (3,), spin2 (3,), D_L, inclination, phi_0, long_asc_nodes, eccentricity, mean_per_ano]
		Warning: last layout (D=14) is made only for compatibility with lalsuite software. The implemented variables are those in D=7 layout; the other are dummy variables and will not be considered.
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
			x_grid = self.times
			if red_grid == False:
				red_grid = True
				warnings.warn("As no grid is given, the default reduced grid is used to evaluate the output. red_grid option is set to True.")

		theta = np.array(theta) #to ensure user theta is copied into new array
		if theta.ndim == 1:
			theta = theta[np.newaxis,:] #(1,D)
		
		D= theta.shape[1] #number of features given
		if D <3:
			raise RuntimeError("Unable to generata WF. Too few parameters given!!")
			return

			#creating a standard theta vector for __get_WF__
		if D>3 and D!=7:
			new_theta = np.zeros((theta.shape[0],7))
			new_theta[:,4] = 1.
			if D== 14:
				if np.any(np.column_stack((theta[:,2:4], theta[:,5:7])) != 0):
					warnings.warn("Given nonzero spin_x/spin_y components. Model currently supports only spin_z component. Other spin components are ignored")
				indices = [0,1,4,7,8,9,10]
				indices_new_theta = range(7)
			else:
				indices = [i for i in range(D)]
				indices_new_theta = indices
		
				#building vector to keep standard layout for __get_WF__
			new_theta[:, indices_new_theta] = theta[:,indices]
			theta = new_theta #(N,7)


			#generating waves and returning to user
		res1, res2 = self.__get_WF__(theta, x_grid, red_grid, plus_cross)
			#res1,res2 = h_plus, h_cross if plus_cross = True
			#res1,res2 = amp, ph if plus_cross = False
		return res1, res2


	def __get_WF__(self, theta, time_grid, red_grid, plus_cross = False):
		"""
	__get_WF__
	==========
		Generates the waves in time domain and perform . Called by get_WF.
		Accepts only input features as [q,s1,s2] or [m1, m2, spin1_z , spin2_z, D_L, inclination, phi_0].
		Input:
			theta (N,D)		source parameters to make prediction at (D=3 or D=7)
			time_grid (D',)	a grid in (physical or reduced) time to evaluate the wave at (uses np.inter)
			red_grid		whether given x_grid is in reduced space (True) or physical space (False)
		Output:
			amp,ph (N,D)	desidered amplitude and phase
		"""
		D= theta.shape[1] #number of features given
		assert D in [3,7] #check that the number of dimension is fine
	
			#setting theta_std & m_tot_us
		if D == 3:
			theta_std = theta
			m_tot_us = 20. * np.ones((theta.shape[0],)) #depending on the convention (ATTENTIOOOOON!!!!!)
		else:
			q = np.divide(theta[:,0],theta[:,1]) #mass ratio (general) (N,)
			m_tot_us = theta[:,0] + theta[:,1]	#total mass in solar masses for the user
			theta_std = np.column_stack((q,theta[:,2],theta[:,3])) #(N,3)

			to_switch = np.where(theta_std[:,0] < 1.) #holds the indices of the events to swap

				#switching masses (where relevant)
			theta_std[to_switch,0] = np.power(theta_std[to_switch,0], -1)
			theta_std[to_switch,1], theta_std[to_switch,2] = theta_std[to_switch,2], theta_std[to_switch,1]

		amp, ph =  self.get_raw_WF(theta_std) #raw WF (N, N_grid)

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
			if (interp_grid[0] < self.times[0]) or (interp_grid[-1] > self.times[-1]):
				if (interp_grid[0] < self.times[0]):
					warnings.warn("Warning: time grid given is too long for the fitted model. Set 0 amplitude outside the fitting domain.")
				indices = np.where(np.logical_or(interp_grid > self.times[-1], interp_grid < self.times[0]) )[0]
				new_amp[i,indices] = 0

		amp = new_amp #amplitude is scaled. to get its original values should be multiplied by 1e-21
		ph = np.subtract(new_ph.T,new_ph[:,0]).T #phase are zero at t = 0

			#### Dealing with distance, inclination and phi_0
		if D==7: #distance corrections are done
			dist_pref = theta[:,4] #std_dist = 1 Mpc
			iota = theta[:,5] #std_inclination = 0.
			phi_0 = theta[:,6] #

				#scaling to required distance
			amp = np.divide(amp.T, dist_pref).T

			#scaling for setting inclination (it is done only if required)
			h_22 = amp*np.exp(1j*(ph)) #choose here a convention... (lal is +)
				#h = h_p +i h_c = Y_22 * h_22 + Y_2-2 * h_2-2
				#h_22 = h*_2-2
				#Y_2+-2 = sqrt(5/(64pi))*(1+-cos(inclination))**2 exp(+-2i phi)
			h = np.multiply(h_22, self.__Y_2m__(2,iota, phi_0)) + np.multiply(np.conj(h_22), self.__Y_2m__(-2,iota, phi_0))
			h = 1e-21*h

			if plus_cross:
				return h.real, h.imag
			else: 
				amp =  np.abs(h) 
				ph = np.unwrap(np.angle(h))
				return amp, ph

		if plus_cross:
			h = 1e-21*amp*np.exp(1j*(ph))
			return h.real, h.imag
		else:
			return 1e-21*amp, ph				

	def __Y_2m__(self,m, iota, phi):
		"""

		"""
		const = 1./4.#np.sqrt(5./(64*np.pi)) #the constant was already fitted in the wave
		c_i = np.cos(iota) #(N,)
		Y_2m = const * np.square(1+np.multiply(np.sign(m), c_i)) #(N,)
		Y_2m = np.multiply(Y_2m, np.exp(1j*np.multiply(np.sign(m), 2*phi)) ) #(N,)
		return Y_2m


	def get_raw_WF(self, theta):
		"""
	get_raw_WF
	==========
		Generates a WF according to the MLGW model with a parameters vector in MLGW model style (params=  [q,s1z,s2z]).
		All waves are evaluated at a luminosity distance of 1 Mpc and inclination 0. They are generated at masses m1 = q * m2 and m2 = 20/(1+q), so that M_tot = 20.
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


	def align_wave(self, amp, ph, x_grid = None, al_merger = True, phi_0=0):
		"""
	align_wave
	==========
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

