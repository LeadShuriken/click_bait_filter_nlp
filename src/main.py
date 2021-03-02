from utils import fillSet, strToSetIndex, vectorize_sequences
from model import save_model, teach_model_k_fold, teach_model_hold_out
from validate import validated_rand, plot_hold_out_res, plot_k_fold_res
from db import remove_db_duplicates

from keras import layers
from keras import models
from keras import regularizers
import subprocess
import numpy as np
import os

modelWordsNumber = 5000
# REMOVING DB DUPLICATES
remove_db_duplicates()

# Exporting data
process = subprocess.run(
    ['./get_data.sh', os.environ['MONGODB_POSITIVE']], cwd=r'./../')
process = subprocess.run(
    ['./get_data.sh', os.environ['MONGODB_NEGATIVE']], cwd=r'./../')

# Fetching Data and indexes
out_data_set = np.array([])
out_data_positive_raw, out_data_set = fillSet(
    out_data_set, '../data/click_bait_db.json')
out_data_negative_raw, out_data_set = fillSet(
    out_data_set, '../data/click_bait_db_negative.json')
out_data_set = {out_data_set[i]: i + 1 for i in range(0, len(out_data_set))}

# To indexes
out_data_positive = strToSetIndex(
    out_data_set, out_data_positive_raw)
out_data_negative = strToSetIndex(
    out_data_set, out_data_negative_raw)

# Removing doubles ... happens
for i, A in np.ndenumerate(out_data_positive):
    for n, B in np.ndenumerate(out_data_negative):
        if np.array_equal(A, B):
            out_data_positive = np.delete(out_data_positive, i)
            out_data_negative = np.delete(out_data_negative, n)

# Mixing
seedInt = np.random.randint(0, 100)
train_data = np.concatenate((
    out_data_positive,
    out_data_negative))
np.random.seed(seedInt)
np.random.shuffle(train_data)

train_labels = np.concatenate((
    np.ones(len(out_data_positive)),
    np.zeros(len(out_data_negative))))
np.random.seed(seedInt)
np.random.shuffle(train_labels)

# Vectorizing Data and Labels
# TODO:On data gathering end
# 1: Change one hot encoding for word embedding
# 2: modelWordsNumber from current longest sequence
x_train = vectorize_sequences(train_data, modelWordsNumber)
y_train = np.asarray(train_labels).astype('float32')

aside = 10
partial_x_train = x_train[:aside]
partial_y_train = y_train[:aside]
train_data = train_data[:aside]

x_train = x_train[aside:]
y_train = y_train[aside:]

# Model
model = models.Sequential()
model.add(layers.Dense(16, kernel_regularizer=regularizers.l2(
    0.001), activation='relu', input_shape=(modelWordsNumber,)))
model.add(layers.Dropout(0.2))
model.add(layers.Dense(
    16, kernel_regularizer=regularizers.l2(0.001), activation='relu'))
model.add(layers.Dropout(0.2))
model.add(layers.Dense(1, activation='sigmoid'))
model.compile(optimizer='rmsprop', loss='binary_crossentropy',
              metrics=['acc'])

history, model, score = teach_model_k_fold(
    model, x_train, y_train, 4, 8, 32)
plot_k_fold_res(history)

# history, model, score = teach_model_hold_out(
#     model, x_train, y_train, 100, 8, 32)
# plot_hold_out_res(history)
print(score)

validated_rand(model, out_data_set, partial_x_train,
               partial_y_train, train_data)
save_model(model, out_data_set)
