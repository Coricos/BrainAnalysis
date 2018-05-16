# DINDIN Meryll
# April 17th, 2018
# Dreem Headband Sleep Phases Classification Challenge

from package.imports import *

# Defines a function to rename the datasets for clearer management
# storage refers to where to pick the dataset
def rename(storage='./dataset'):

    train_pth = '{}/train.h5'.format(storage)
    valid_pth = '{}/valid.h5'.format(storage)

    for pth in [train_pth, valid_pth]:

        with h5py.File(pth, 'a') as dtb:

            dtb['acc_x'] = dtb['accelerometer_x']
            del dtb['accelerometer_x']
            dtb['acc_y'] = dtb['accelerometer_y']
            del dtb['accelerometer_y']
            dtb['acc_z'] = dtb['accelerometer_z']
            del dtb['accelerometer_z']

# Display a specific 30s sample
# idx refers to the index of the sample
def display(idx, storage='./dataset/valid.h5'):

    with h5py.File(storage, 'r') as dtb:
        # Load the signals
        a_x = dtb['acc_x'][idx,:]
        a_y = dtb['acc_y'][idx,:]
        a_z = dtb['acc_z'][idx,:]
        n_a = np.sqrt(np.square(a_x) + np.square(a_y) + np.square(a_z))
        e_1 = dtb['eeg_1'][idx,:]
        e_2 = dtb['eeg_2'][idx,:]
        e_3 = dtb['eeg_3'][idx,:]
        e_4 = dtb['eeg_4'][idx,:]
        o_i = dtb['po_ir'][idx,:]
        o_r = dtb['po_r'][idx,:]

    # Defines the figure
    plt.figure(figsize=(18,10))
    fig = gs.GridSpec(4, 12)
    plt.subplot(fig[0, 0:4])
    plt.plot(a_x, label='Acc_X')
    plt.legend(loc='best')
    plt.grid()
    plt.subplot(fig[0, 4:8])
    plt.plot(a_y, label='Acc_Y')
    plt.legend(loc='best')
    plt.grid()
    plt.subplot(fig[0, 8:12])
    plt.plot(a_z, label='Acc_X')
    plt.legend(loc='best')
    plt.grid()
    plt.subplot(fig[1, :])
    plt.plot(n_a, label='Normed_Acc')
    plt.legend(loc='best')
    plt.grid()
    plt.subplot(fig[2, 0:3])
    plt.plot(e_1, label='EEG_1')
    plt.legend(loc='best')
    plt.grid()
    plt.subplot(fig[2, 3:6])
    plt.plot(e_2, label='EEG_2')
    plt.legend(loc='best')
    plt.grid()
    plt.subplot(fig[2, 6:9])
    plt.plot(e_3, label='EEG_3')
    plt.legend(loc='best')
    plt.grid()
    plt.subplot(fig[2, 9:12])
    plt.plot(e_4, label='EEG_4')
    plt.legend(loc='best')
    plt.grid()
    plt.subplot(fig[3, 0:6])
    plt.plot(o_i, label='Oxygen_IR')
    plt.legend(loc='best')
    plt.grid()
    plt.subplot(fig[3, 6:12])
    plt.plot(o_r, label='Oxygen_R')
    plt.legend(loc='best')
    plt.grid()
    plt.tight_layout()
    plt.show()

# Defines the kalman filter for noise reduction
# std_factor refers to the sought reduction of deviation of the signal
# smooth_window refers to the convolution window for smoothing
def kalman_filter(val, std_factor=3, smooth_window=5):

    # Initialize the arrays
    x_t = np.zeros(val.shape[0])
    P_t = np.zeros(val.shape[0])
    x_m = np.zeros(val.shape[0])
    P_m = np.zeros(val.shape[0])
    fac = np.zeros(val.shape[0])
    # Defines the variables
    R = (np.std(val))**2
    Q = (np.std(val) / std_factor)**2
    tmp = np.nanmean(val[:5])
    if np.isnan(tmp): x_t[0] = np.nanmean(val)
    else: x_t[0] = tmp    
    P_t[0] = np.std(val)

    # Iterative construction
    for k in range(1, val.shape[0]):
        x_m[k] = x_t[k-1]
        P_m[k] = P_t[k-1] + Q
        fac[k] = P_m[k] / (P_m[k] + R)
        x_t[k] = x_m[k] + fac[k] * (val[k] - x_m[k])
        P_t[k] = (1 - fac[k]) * P_m[k]

    # Apply smoothing
    b = np.full(smooth_window, 1.0 / smooth_window)
    x_t = sg.lfilter(b, 1, x_t)

    # Memory efficiency
    del P_t, x_m, P_m, fac, R, Q
    
    return x_t

# Defines a multiprocessed oriented call to build the acceleration norm
# vec_x refers to the first component
# vec_y refers to the second component
# vec_z refers to the third component
def get_norm(vec_x, vec_y, vec_z):

    return np.sqrt(np.square(vec_x) + np.square(vec_y) + np.square(vec_z))

# Defines a vector reduction through interpolation
# val refers to a 1D array
# size refers to the desired size
def interpolate(val, size=2000):

    # Defines whether the size is determined or not
    x = np.linspace(0, size, num=len(val), endpoint=True)
    o = np.linspace(0, size, num=size, endpoint=True)

    if len(val) < size:
        f = interp1d(x, val, kind='linear', fill_value='extrapolate')
        return f(o)

    if len(val) == size:
        return val

    if len(val) > size:
        f = interp1d(x, val, kind='cubic')
        return f(o)

# Compute the fft components
# val refers to a 1D array
# n_components refers to the desired amounts of components
def compute_fft(val, n_components=50):

    return np.abs(np.fft.rfft(val))[:n_components]
