# DINDIN Meryll
# May 17th, 2018
# Dreem Headband Sleep Phases Classification Challenge

from package.toolbox import *

class Database:

    # Initialization
    # storage refers to where to get the datasets
    def __init__(self, storage='./dataset'):

        self.train_pth = '{}/train.h5'.format(storage)
        self.valid_pth = '{}/valid.h5'.format(storage)
        self.train_out = '{}/dts_train.h5'.format(storage)
        self.valid_out = '{}/dts_valid.h5'.format(storage)
        self.train_sca = '{}/sca_train.h5'.format(storage)
        self.valid_sca = '{}/sca_valid.h5'.format(storage)

        self.storage = storage
        self.sets_size = []
        
        with h5py.File(self.train_pth, 'r') as dtb:
            self.sets_size.append(dtb['po_r'].shape[0])
            self.keys = list(dtb.keys())
        with h5py.File(self.valid_pth, 'r') as dtb:
            self.sets_size.append(dtb['po_r'].shape[0])

    # Apply filtering and interpolation on the samples
    # sampling_freq refers to the desired sampling frequency
    # out_storage refers to where to put the newly build datasets
    def build(self, sampling_freq=100, out_storage='/mnt/Storage'):

        # Defines the parameters for each key
        fil = {'po_r': True, 'po_ir': True,
               'acc_x': False, 'acc_y': False, 'acc_z': False,
               'eeg_1': True, 'eeg_2': True, 'eeg_3': True, 'eeg_4': True}

        dic = {'eeg_1': (4, 20), 'eeg_2': (4, 20), 'eeg_3': (4, 20),
               'eeg_4': (4, 20), 'po_ir': (3, 5), 'po_r': (3, 5)}

        # Iterates over the keys
        for key in tqdm.tqdm(fil.keys()):
            # Link inputs to outputs
            for pth, out in zip([self.train_pth, self.valid_pth], 
                                [self.train_out, self.valid_out]):
                # Load the values
                with h5py.File(pth, 'r') as dtb: val = dtb[key].value

                # Apply the kalman filter if needed
                if fil[key]:
                    pol = multiprocessing.Pool(processes=multiprocessing.cpu_count())
                    arg = {'std_factor': dic[key][0], 'smooth_window': dic[key][1]}
                    fun = partial(kalman_filter, **arg)
                    val = np.asarray(pol.map(fun, val))
                    pol.close()
                    pol.join()

                # Adapt the size of the vectors
                pol = multiprocessing.Pool(processes=multiprocessing.cpu_count())
                fun = partial(interpolate, size=30*sampling_freq)
                val = np.asarray(pol.map(fun, val))
                pol.close()
                pol.join()

                # Serialize the outputs
                with h5py.File(out, 'a') as dtb:
                    if dtb.get(key): del dtb[key]
                    dtb.create_dataset(key, data=val)

                # Memory efficiency
                del pol, fun, val

    # Load the corresponding labels
    # input refers to the input_file in which the labels are stored
    def load_labels(self, input):

        lab = pd.read_csv(input, sep=';', index_col=0)

        with h5py.File(self.train_out, 'a') as dtb:
            # Serialize the labels
            if dtb.get('lab'): del dtb['lab']
            dtb.create_dataset('lab', data=lab.values)

    # Build the norm of the accelerometers
    def add_norm_acc(self):

        # Iterates over both the training and validation sets
        for pth in [self.train_out, self.valid_out]:

            with h5py.File(pth, 'r') as dtb:

                # Aggregates the values
                tmp = np.square(dtb['acc_x'].value)
                tmp += np.square(dtb['acc_y'].value)
                tmp += np.square(dtb['acc_z'].value)

            # Serialize the result
            with h5py.File(pth, 'a') as dtb:

                if dtb.get('norm_acc'): del dtb['norm_acc']
                dtb.create_dataset('norm_acc', data=np.sqrt(tmp))

            # Memory efficiency
            del tmp

    # Build the norm of the ECGs
    def add_norm_eeg(self):

        # Iterates over both the training and validation sets
        for pth in [self.train_out, self.valid_out]:

            with h5py.File(pth, 'r') as dtb:

                # Aggregates the values
                tmp = np.square(dtb['eeg_1'].value)
                tmp += np.square(dtb['eeg_2'].value)
                tmp += np.square(dtb['eeg_3'].value)
                tmp += np.square(dtb['eeg_4'].value)

            # Serialize the result
            with h5py.File(pth, 'a') as dtb:

                if dtb.get('norm_eeg'): del dtb['norm_eeg']
                dtb.create_dataset('norm_eeg', data=np.sqrt(tmp))

            # Memory efficiency
            del tmp

    def add_betti_curves(self):

        for pth in [self.train_out, self.valid_out]:

            res = []
            # Iterates over the keys
            for key in tqdm.tqdm(range(1, 5)):

                # Load the corresponding values
                with h5py.File(pth, 'r') as dtb: 
                    val = dtb['eeg_{}'.format(key)].value
                    
                # Multiprocessed computation
                pol = multiprocessing.Pool(processes=multiprocessing.cpu_count())
                res = np.asarray(pol.map(compute_betti_curves, val))
                pol.close()
                pol.join()

                # Serialize the output
                with h5py.File(pth, 'a') as dtb:
                    key = 'bup_{}'.format(key)
                    if dtb.get(key): del dtb[key]
                    dtb.create_dataset(key, data=res[:,0,:])
                    key = 'bdw_{}'.format(key)
                    if dtb.get(key): del dtb[key]
                    dtb.create_dataset(key, data=res[:,1,:])

    # Adds the wavelet transformations
    def add_wavelets(self):

        for pth in [self.train_out, self.valid_out]:

            res = []
            # Iterates over the keys
            for key in tqdm.tqdm(range(1, 5)):

                # Load the corresponding values
                with h5py.File(pth, 'r') as dtb: 
                    val = dtb['eeg_{}'.format(key)].value
                    
                # Multiprocessed computation
                pol = multiprocessing.Pool(processes=multiprocessing.cpu_count())
                res = np.asarray(pol.map(compute_wavelet, val))
                pol.close()
                pol.join()

                # Serialize the output
                with h5py.File(pth, 'a') as dtb:
                    key = 'wav_{}'.format(key)
                    if dtb.get(key): del dtb[key]
                    dtb.create_dataset(key, data=res)

    # Build the features for each channel
    def add_features(self):

        lst = ['norm_acc', 'norm_eeg', 'po_r', 'po_ir', 'eeg_1', 'eeg_2', 'eeg_3', 'eeg_4']

        for pth in [self.train_out, self.valid_out]:

            res = []
            # Iterates over the keys
            for key in tqdm.tqdm(lst):

                # Load the corresponding values
                with h5py.File(pth, 'r') as dtb: val = dtb[key].value
                # Multiprocessed computation
                pol = multiprocessing.Pool(processes=multiprocessing.cpu_count())
                res.append(np.asarray(pol.map(compute_features, val)))
                pol.close()
                pol.join()

            # Serialize the output
            with h5py.File(pth, 'a') as dtb:
                if dtb.get('fea'): del dtb['fea']
                dtb.create_dataset('fea', data=np.hstack(tuple(res)))

    # Add the PCA construction of all the vectors
    # n_components refers to the amount of components to extract
    def add_pca(self, n_components=10):

        lst = ['norm_acc', 'norm_eeg', 'po_r', 'po_ir', 'eeg_1', 'eeg_2', 'eeg_3', 'eeg_4']
        train_pca, valid_pca = [], []

        # Iterates over the keys
        for key in tqdm.tqdm(lst):

            # Defines the PCA transform adapted to incremental learning
            pca = IncrementalPCA(n_components=n_components)
            # Partial fit over training and validation
            for pth in [self.train_out, self.valid_out]:
                with h5py.File(pth, 'r') as dtb:
                    pca.partial_fit(dtb[key].value)
            # Apply transformation on training set
            with h5py.File(self.train_out, 'r') as dtb:
                train_pca.append(pca.transform(dtb[key].value))
            # Apply transformation on validation set
            with h5py.File(self.valid_out, 'r') as dtb:
                valid_pca.append(pca.transform(dtb[key].value))

        # Serialization for the training results
        with h5py.File(self.train_out, 'a') as dtb:
            if dtb.get('pca'): del dtb[pca]
            dtb.create_dataset('pca', data=np.hstack(tuple(train_pca)))
        # Serialization for the validation results
        with h5py.File(self.valid_out, 'a') as dtb:
            if dtb.get('pca'): del dtb[pca]
            dtb.create_dataset('pca', data=np.hstack(tuple(valid_pca)))

    # Apply the chaos theory features on the different vectors
    def add_chaos(self):

        lst = ['eeg_1', 'eeg_2', 'eeg_3', 'eeg_4']

        for pth in [self.train_out, self.valid_out]:

            res = []
            # Iterates over the keys
            for key in tqdm.tqdm(lst):

                # Load the corresponding values
                with h5py.File(pth, 'r') as dtb: val = dtb[key].value
                # Multiprocessed computation
                pol = multiprocessing.Pool(processes=multiprocessing.cpu_count())
                res.append(np.asarray(pol.map(compute_chaos, val)))
                pol.close()
                pol.join()

            # Serialize the output
            with h5py.File(pth, 'a') as dtb:
                if dtb.get('chaos'): del dtb['chaos']
                dtb.create_dataset('chaos', data=np.hstack(tuple(res)))

    # Rescale the datasets considering both training and validation
    def rescale(self):

        with h5py.File(self.train_out, 'r') as dtb:
            tem = ['acc_x', 'acc_y', 'acc_z', 
                   'norm_acc', 'norm_eeg', 
                   'eeg_1', 'eeg_2', 'eeg_3', 'eeg_4', 
                   'po_r', 'po_ir',
                   'wav_1', 'wav_2', 'wav_3', 'wav_4',
                   'bup_1', 'bup_2', 'bup_3', 'bup_4',
                   'bdw_1', 'bdw_2', 'bdw_3', 'bdw_4']
            env = ['eeg_1', 'eeg_2', 'eeg_3', 'eeg_4', 'po_r', 'po_ir']
            lst = list(dtb.keys())
            oth = [key for key in lst if key not in tem + ['lab']]

        # Apply the logarithmic envelope
        for key in lst:

            if key in env:

                # Load the data from both the training and validation sets
                with h5py.File(self.train_out, 'r') as dtb:
                    v_t = dtb[key].value
                with h5py.File(self.valid_out, 'r') as dtb:
                    v_v = dtb[key].value

                # Apply the transformation
                m_x = max(np.max(v_t), np.max(v_v))
                coe = list(np.max(v_t, axis=1)) + list(np.max(v_v, axis=1))
                coe = np.median(np.asarray(coe))

                pol = multiprocessing.Pool(processes=multiprocessing.cpu_count())
                fun = partial(envelope, m_x=m_x, coeff=coe)
                v_t = np.asarray(pol.map(fun, v_t))
                pol.close()
                pol.join()

                pol = multiprocessing.Pool(processes=multiprocessing.cpu_count())
                fun = partial(envelope, m_x=m_x, coeff=coe)
                v_v = np.asarray(pol.map(fun, v_v))
                pol.close()
                pol.join()

                # Serialize and replace
                with h5py.File(self.train_sca, 'a') as dtb:
                    if dtb.get(key): del dtb[key]
                    dtb.create_dataset(key, data=v_t)
                with h5py.File(self.valid_sca, 'a') as dtb:
                    if dtb.get(key): del dtb[key]
                    dtb.create_dataset(key, data=v_v)

                # Memory efficiency
                del v_t, v_v

            else:

                with h5py.File(self.train_sca, 'a') as dtb:
                    if dtb.get(key): del dtb[key]
                    with h5py.File(self.train_out, 'r') as inp:
                        dtb.create_dataset(key, data=inp[key].value)

                if key != 'lab':

                    with h5py.File(self.valid_sca, 'a') as dtb:
                        if dtb.get(key): del dtb[key]
                        with h5py.File(self.valid_out, 'r') as inp:
                            dtb.create_dataset(key, data=inp[key].value)

        # Specific scaling for temporal units
        for key in tqdm.tqdm(tem):

            # Defines the scalers
            mms = MinMaxScaler(feature_range=(0,1))
            sts = StandardScaler(with_std=False)

            for pth in [self.train_sca, self.valid_sca]:
                # Partial fit for both training and validation
                with h5py.File(pth, 'r') as dtb:
                    mms.partial_fit(np.hstack(dtb[key].value).reshape(-1,1))

            for pth in [self.train_sca, self.valid_sca]:
                # Partial fit for both training and validation
                with h5py.File(pth, 'r') as dtb:
                    tmp = mms.transform(np.hstack(dtb[key].value).reshape(-1,1))
                    sts.partial_fit(tmp)
                    del tmp

            # Concatenate the pipeline of scalers
            pip = Pipeline([('mms', mms), ('sts', sts)])

            for pth in [self.train_sca, self.valid_sca]:
                # Apply transformation
                with h5py.File(pth, 'a') as dtb:
                    shp = dtb[key].shape
                    tmp = np.hstack(dtb[key].value).reshape(-1,1)
                    res = pip.transform(tmp).reshape(shp)
                    # Rescale to independant zero mean
                    zmn = StandardScaler(with_std=False)
                    res = zmn.fit_transform(np.transpose(res))
                    dtb[key][...] = np.transpose(res)

            # Memory efficiency
            del mms, sts, pip, tmp, zmn

        # Specific scaling for features datasets
        for key in tqdm.tqdm(oth):

            # Build the scaler
            mms = MinMaxScaler(feature_range=(-1,1))
            sts = StandardScaler(with_std=False)

            for pth in [self.train_sca, self.valid_sca]:
                # Partial fit for both training and validation
                with h5py.File(pth, 'r') as dtb:
                    mms.partial_fit(dtb[key].value)

            for pth in [self.train_sca, self.valid_sca]:
                # Partial fit for both training and validation
                with h5py.File(pth, 'r') as dtb:
                    sts.partial_fit(mms.transform(dtb[key].value))

            pip = Pipeline([('mms', mms), ('sts', sts)])

            for pth in [self.train_sca, self.valid_sca]:
                # Transformation for both training and validation
                with h5py.File(pth, 'a') as dtb:
                    dtb[key][...] = pip.transform(dtb[key].value)

    # Defines a way to reduce the problem
    # output refers to where to serialize the output database
    # size refers to the amount of vectors to keep
    def truncate(self, output, size=3000):

        with h5py.File(self.train_sca, 'r') as inp:

            # Defines the indexes for extraction
            arg = {'size': size, 'replace': False}
            idx = np.random.choice(np.arange(inp['acc_x'].shape[0]), **arg)

            with h5py.File(output, 'a') as out:

                for key in tqdm.tqdm(list(inp.keys())):
                    # Iterated serialization of the key component
                    out.create_dataset(key, data=inp[key].value[idx])

    # Defines both training and testing instances
    # output refers to where to put the data
    # test refers to the test_size
    def preprocess(self, output, test=0.3):

        # Split the training set into both training and testing
        with h5py.File(self.train_sca, 'r') as dtb:

            idx = np.arange(dtb['lab'].shape[0])
            arg = {'test_size': test, 'shuffle': True}
            i_t, i_e, _, _ = train_test_split(idx, idx, **arg)
            i_t = shuffle(i_t)

            for key in tqdm.tqdm(list(dtb.keys())):

                with h5py.File(output, 'a') as out:

                    lab_t, lab_e = '{}_t'.format(key), '{}_e'.format(key)

                    if out.get(lab_t): del out[lab_t]
                    out.create_dataset(lab_t, data=dtb[key].value[i_t])
                    if out.get(lab_e): del out[lab_e]
                    out.create_dataset(lab_e, data=dtb[key].value[i_e])

        # Adds the validation set into the output database
        with h5py.File(self.valid_sca, 'r') as dtb:

            for key in tqdm.tqdm(list(dtb.keys())):

                with h5py.File(output, 'a') as out:

                    lab_v = '{}_v'.format(key)

                    if out.get(lab_v): del out[lab_v]
                    out.create_dataset(lab_v, data=dtb[key].value)
        