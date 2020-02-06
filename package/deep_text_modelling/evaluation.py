import os
import numpy as np
import xarray as xr
import pandas as pd
from keras import backend as K
import matplotlib.pyplot as plt
from itertools import islice
from pyndl import io

def score_given_metric(y_true, y_pred, metric):

    """ calculate the performance score given a keras-defined metric

    Parameters
    ----------
    y_true: numpy array
        array containing the true labels
    y_pred: numpy array
        array containing the predicted labels
    metric: function
        peformance metric defined to work with keras models 

    Returns
    -------
    float
        performance based on a given metric
    """
   
    y_t = K.variable(y_true)
    y_p = K.variable(y_pred)
    output = metric(y_t, y_p)
    return K.eval(output)

def recall(y_true, y_pred):

    """ calculate the recall performance for keras models

    Parameters
    ----------
    y_true: numpy array
        array containing the true labels
    y_pred: numpy array
        array containing the predicted labels

    Returns
    -------
    Keras tensor
        recall performance
    Note
    ----
    The recall measure is calculated globally by counting the total true positives (corresponds to average = 'micro' in sklearn)
    """

    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall

def precision(y_true, y_pred):

    """ calculate the precision performance for keras models

    Parameters
    ----------
    y_true: numpy array
        array containing the true labels
    y_pred: numpy array
        array containing the predicted labels

    Returns
    -------
    Keras tensor
        precision performance
    Note
    ----
    The precision measure is calculated globally by counting the total true and predicted positives (corresponds to average = 'micro' in sklearn)
    """

    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision

def f1score(y_true, y_pred):

    """ calculate the F1-score for keras models

    Parameters
    ----------
    y_true: numpy array
        array containing the true labels
    y_pred: numpy array
        array containing the predicted labels

    Returns
    -------
    Keras tensor
        F1-score 
    Note
    ----
    The F1 measure is calculated globally by counting the total true and predicted positives (corresponds to average = 'micro' in sklearn)
    """

    pr = precision(y_true, y_pred)
    re = recall(y_true, y_pred)
    return 2 * ((pr*re) / (pr+re+K.epsilon()))

def predict_proba_eventfile_FNN(model, data_test, num_cues, num_outcomes, cue_index, 
                                outcome_index, generator, use_multiprocessing = False, 
                                num_threads = 0, verbose = 0):

    """ extract the most likely outcomes based on a 1d-array of predicted probabilities 

    Parameters
    ----------
    model: class
        keras model output
    data_test: dataframe or class
        dataframe or indexed text file containing test data
    num_cues: int
        number of allowed cues
    num_outcomes: int
        number of allowed outcomes
    cue_index: dict
        mapping from cues to indices
    outcome_index: dict
        mapping from outcomes to indices
    generator: class
        use 'generator = generator_df_FNN' if the data is given as a dataframe or 
        'generator = generator_textfile_FNN' if the data is given as an indexed file 
    use_multiprocessing: Boolean
        whether to generate batches in parallel. Default: False
    num_threads: int
        maximum number of processes to spin up when using generating the batches. Default: 0
    verbose: int (0, 1, or 2)
        verbosity mode. 0 = silent, 1 = progress bar, 2 = one line per epoch.

    Returns
    -------
    numpy array
        array containing the predicted probabilities
    """

    #from deep_text_modelling.modelling import generator_textfile_FNN

    test_gen = generator(data = data_test, 
                         batch_size = 1,
                         num_cues = num_cues,
                         num_outcomes = num_outcomes,
                         cue_index = cue_index,
                         outcome_index = outcome_index,
                         shuffle = False)

    proba_pred = model.predict_generator(test_gen,
                                         use_multiprocessing = use_multiprocessing, 
                                         workers = num_threads,
                                         verbose = verbose)
    return proba_pred

def predict_proba_oneevent_FNN(model, cue_seq, num_cues, cue_index):

    """ extract the most likely outcomes based on a 1d-array of predicted probabilities 

    Parameters
    ----------
    model: class
        keras model output
    cue_seq: str
        underscore-seperated sequence of cues
    num_cues: int
        number of allowed cues
    cue_index: dict
        mapping from cues to indices

    Returns
    -------
    numpy 1d-array
        array containing the predicted probabilities
    """

    from deep_text_modelling.modelling import seq_to_onehot_1darray

    cue_onehot = seq_to_onehot_1darray(cue_seq, index_system = cue_index, N_tokens = num_cues)
    cue_onehot = np.expand_dims(cue_onehot, 0)
    proba_pred = np.squeeze(model.predict(x = cue_onehot, batch_size = 1))

    return proba_pred

def predict_proba_eventfile_LSTM(model, data_test, num_cues, num_outcomes, cue_index, 
                                 outcome_index, max_len, generator, use_multiprocessing = False, 
                                 num_threads = 0, verbose = 0):

    """ extract the most likely outcomes based on a 1d-array of predicted probabilities 

    Parameters
    ----------
    model: class
        keras model output
    data_test: dataframe or class
        dataframe or indexed text file containing test data
    num_cues: int
        number of allowed cues
    num_outcomes: int
        number of allowed outcomes
    cue_index: dict
        mapping from cues to indices
    outcome_index: dict
        mapping from outcomes to indices
    max_len: int
        Consider only 'max_len' first tokens in a sequence
    generator: class
        use 'generator = generator_df_LSTM' if the data is given as a dataframe or 
        'generator = generator_textfile_LSTM' if the data is given as an indexed file 
    use_multiprocessing: Boolean
        whether to generate batches in parallel. Default: False
    num_threads: int
        maximum number of processes to spin up when using generating the batches. Default: 0
    verbose: int (0, 1, or 2)
        verbosity mode. 0 = silent, 1 = progress bar, 2 = one line per epoch.

    Returns
    -------
    numpy array
        array containing the predicted probabilities
    """

    #from deep_text_modelling.modelling import generator_textfile_FNN

    test_gen = generator(data = data_test, 
                         batch_size = 1,
                         num_cues = num_cues,
                         num_outcomes = num_outcomes,
                         cue_index = cue_index,
                         outcome_index = outcome_index,
                         max_len = max_len,
                         shuffle = False)

    proba_pred = model.predict_generator(test_gen,
                                         use_multiprocessing = use_multiprocessing, 
                                         workers = num_threads,
                                         verbose = verbose)
    return proba_pred

def predict_proba_oneevent_LSTM(model, cue_seq, num_cues, cue_index, max_len):

    """ extract the most likely outcomes based on a 1d-array of predicted probabilities 

    Parameters
    ----------
    model: class
        keras model output
    cue_seq: str
        underscore-seperated sequence of cues
    num_cues: int
        number of allowed cues
    cue_index: dict
        mapping from cues to indices
    max_len: int
        Consider only 'max_len' first tokens in a sequence

    Returns
    -------
    numpy 1d-array
        array containing the predicted probabilities
    """

    from deep_text_modelling.modelling import seq_to_onehot_2darray

    cue_onehot = seq_to_onehot_2darray(cue_seq, index_system = cue_index, N_tokens = num_cues, max_len = max_len)
    cue_onehot = np.expand_dims(cue_onehot, 0)
    proba_pred = np.squeeze(model.predict(x = cue_onehot, batch_size = 1))

    return proba_pred

def top_predicted_outcomes(proba_pred, index_to_outcome_dict, N_top = 3):

    """ extract the most likely outcomes based on a 1d-array of predicted probabilities 

    Parameters
    ----------
    proba_pred: numpy 1d-array
        array containing the predicted probabilities
    index_to_outcome_dict: dict
        reversed index systen for the outcomes

    Returns
    -------
    dict
        top outcomes along with their probability of occurrences
    """

    # extract the indices of the top 'N_top' outcomes 
    idxs_top = np.argsort(proba_pred)[::-1][:N_top] 
    # top outcomes
    top_outcomes = {index_to_outcome_dict[i+1]:proba_pred[i] for i in idxs_top}
    return top_outcomes

def plot_learning_curve(history_dict, metric = 'acc', set = 'train'):

    """ plot learning curve given a keras history object and a metric

    Parameters
    ----------
    history: class
        keras history object
    metric: str
        performance metric to use ('loss', 'acc', 'precision', 'recall', 'f1score')
    set: str
        'train' or 'valid' or 'train_valid'

    Returns
    -------
    None
        generate a matplotlib graph
    """

    # Extract the performance vector
    if set == 'train':

        metric_code = metric 
        perform_vect = history_dict[metric_code]
        epochs = range(1, len(perform_vect) + 1)

        # Plotting metric over epochs 
        plt.plot(epochs, perform_vect, 'b') # "b" is for "solid blue line"
        plt.title('Training ' + metric)
        plt.xlabel('Epochs')
        plt.ylabel(metric)
        plt.legend()
        plt.show()

    if set == 'valid':

        metric_code = 'val_' + metric 
        perform_vect = history_dict[metric_code]
        epochs = range(1, len(perform_vect) + 1)

        # Plotting metric over epochs 
        plt.plot(epochs, perform_vect, 'b') # "b" is for "solid blue line"
        plt.title('Validation ' + metric)
        plt.xlabel('Epochs')
        plt.ylabel(metric)
        plt.legend()
        plt.show()

    if set == 'train_valid':

        metric_code_train = metric 
        metric_code_valid = 'val_' + metric 
        perform_vect_train = history_dict[metric_code_train]
        perform_vect_valid = history_dict[metric_code_valid]
        epochs = range(1, len(perform_vect_train) + 1)

        # Plotting loss over epochs 
        plt.plot(epochs, perform_vect_train, 'r', label = 'training') #  "r" is for "solid red line"
        plt.plot(epochs, perform_vect_valid, 'b', label = 'validation') # "b" is for "solid blue line"
        plt.title('Training and validation ' + metric)
        plt.xlabel('Epochs')
        plt.ylabel(metric)
        plt.legend()
        plt.show()

def activations_to_proba(activations, T = 1):

    """
    convert activations to probabilities using softmax function

    Parameters
    ----------
    activations: xarray.DataArray or numpy.ndarray
        matrix of activations 
    T: float
        temperature hyperparameter to adjust the confidence in the predictions from the activations.
        Low values increase the confidence in the predictions. 

    Returns
    -------
    numpy 2D-array
        array of dim (num_events * num_outcomes), which contains, for each event, the probabilities 
        of the different outcomes
    """

    if isinstance(activations, np.ndarray):
        e_acts = xr.ufuncs.exp((activations - np.max(activations))/T)
        softmax = e_acts / e_acts.sum()
        return softmax
    elif isinstance(activations, xr.DataArray):
        e_acts = xr.ufuncs.exp((activations - xr.DataArray.max(activations))/T)
        softmax = e_acts / e_acts.sum(axis = 1)
        return softmax.transpose()
    else:
        raise('the activation matrix should be either an xarray.DataArray or a numpy.ndarray')
    
    
def activations_to_predictions(activations):

    """
    convert activations to probabilities using softmax function

    Parameters
    ----------
    activations: xarray.DataArray
        matrix of activations of dim (num_events * num_outcomes)

    Returns
    -------
    list
        predicted outcomes for all events 
    """

    # Predicted tenses from the activations 
    y_pred = []
    for j in range(activations.shape[1]):
        activation_col = activations[:, j]
        argmax_j = activation_col.where(activation_col == activation_col.max(), drop=True).squeeze().coords['outcomes'].values.item()
        y_pred.append(argmax_j)
    return y_pred

def chunk(iterable, chunksize):
    
    """Returns lazy iterator that yields chunks from iterable.
    """

    iterator = iter(iterable)
    return iter(lambda: list(islice(iterator, chunksize)), [])

def predict_outcomes_NDL(data_test, weights, temp_dir, chunksize, num_threads = 1):

    """compute outcome predictions by going through the corpus in chunks for memory efficiency"""

    from pyndl.activation import activation
    from deep_text_modelling.preprocessing import df_to_gz

    ### Path to the train event file
    if isinstance(data_test, str):     
        events_test_path = data_test
    elif isinstance(data_test, pd.DataFrame):
        if temp_dir:
            events_test_path = os.path.join(temp_dir, 'data_test_temp.gz')
            df_to_gz(data = data_test, gz_outfile = events_test_path)
        else: 
            raise ValueError("provide a path to a temporary directory for generating a temporary .gz event file")
    else:
        raise ValueError("data_test should be either a path to an event file or a dataframe")

    y_pred = []
    events = io.events_from_file(events_test_path)
    for events_chunk in chunk(events, chunksize):
        activations = activation(events = events_chunk, 
                                 weights = weights,
                                 number_of_threads = num_threads,
                                 remove_duplicates = True,
                                 ignore_missing_cues = True)
        # Predicted outcomes from the activations
        y_pred.extend(activations_to_predictions(activations)) 
    return y_pred

def predict_proba_oneevent_NDL(model, cue_seq, remove_duplicates = True, T = 1):

    """ Compute predicted outcome probabilities for NDL for one event using softmax 

    Parameters
    ----------
    model: class
        ndl model output
    cue_seq: str
        underscore-seperated sequence of cues
    remove_duplicates: boolean
        Whether to remove repeated cues in the event (True) of not (False)
    T: float
        temperature hyperparameter to adjust the confidence in the predictions from the activations.
        Low values increase the confidence in the predictions. Default = 1, corresponds to a standard 
        softmax transformation 

    Returns
    -------
    numpy 1d-array
        array containing the predicted probabilities
    """

    from deep_text_modelling.evaluation import activations_to_proba

    ### Extract the cue tokens 
    cues = cue_seq.split('_')

    # Remove duplicates if asked for
    if remove_duplicates:
        cues = list(set(cues))

    ### Ignore_missing cues:
    all_cues = model.weights.coords["cues"].values.tolist()
    cues = [cue for cue in cues if cue in all_cues]

    ### Compute the activations for all outcomes based on the cues that appear in the weight matrix
    activations = model.weights.loc[{'cues': cues}].values.sum(axis=1)

    ### Convert to the activations to probabilities
    proba_pred = activations_to_proba(activations, T = T)

    return proba_pred

def predict_proba_eventfile_NDL(model, data_test, temp_dir = None, T = 1, num_threads = 1):

    """ Generate predicted probabilities for NDL

    Parameters
    ----------
    model: class
        NDL model outputs (contains weights and activations)
    data_test: dataframe or class
        dataframe or indexed text file containing test data
    temp_dir: str
        directory where to store the converted gz file if a dataframe is passed to data_test 
        (needed to compute the activation matrix)
    T: float
        temperature hyperparameter to adjust the confidence in the predictions from the activations.
        Low values increase the confidence in the predictions. 
    num_threads: int
        maximum number of processes to use when computing the activations is the data is unseen. Default: 1

    Returns
    -------
    numpy array
        array containing the predicted probabilities 
    """

    from pyndl.activation import activation
    from deep_text_modelling.preprocessing import df_to_gz

    ### Path to the train event file
    if isinstance(data_test, str):     
        events_test_path = data_test
    elif isinstance(data_test, pd.DataFrame):
        if temp_dir:
            events_test_path = os.path.join(temp_dir, 'data_test_temp.gz')
            df_to_gz(data = data_test, gz_outfile = events_test_path)
        else: 
            raise ValueError("provide a path to a temporary directory for generating a temporary .gz event file")
    else:
        raise ValueError("data_test should be either a path to an event file or a dataframe")

    # Generate the activations 
    activations_test = activation(events = events_test_path, 
                                  weights = model.weights,
                                  number_of_threads = num_threads,
                                  remove_duplicates = True,
                                  ignore_missing_cues = True)

    # Predicted probabilities using softmax
    proba_pred = activations_to_proba(activations = activations_test, T = T)
    return proba_pred
 
