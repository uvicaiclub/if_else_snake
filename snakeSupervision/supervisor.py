# Train a model to predict if player 0 will win a battlesnake game given a game state.
import argparse
import json

import keras
import numpy as np
from keras.layers import Conv1D, Dense, Flatten, MaxPool1D, Reshape
from keras.models import Sequential

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', default='basicModel.h5')
args = parser.parse_args()

# loads training examples from json file
def getTrainingExamples():
    trainingExamples = []
    with open("trainingExamples.json") as json_file:
        for line in json_file:
            trainingExamples.append(json.loads(line))
    return trainingExamples


# loads training labels from json file
def getTrainingLabels():
    with open("trainingLabels.json") as json_file:
        trainingLabels = [int(c) for c in json_file.read()]
    return trainingLabels

if args.model == 'basicModel.h5':
    # Basic net
    model = Sequential()
    model.add(Dense(30, activation='relu', input_dim=609))
    model.add(Dense(30, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
else:
    # Conv net
    model = Sequential()
    model.add(Reshape((609, 1), input_shape=(609,)))
    model.add(Conv1D(32, kernel_size=3, activation='relu'))
    model.add(MaxPool1D(pool_size=2))
    model.add(Flatten())
    model.add(Dense(64, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))

# compiles model
model.compile(optimizer='adam',
              loss='binary_crossentropy',
              metrics=['accuracy'])

# formats training examples into a numpy array
trainingExamples = np.asarray(getTrainingExamples())
trainingLabels = np.asarray(getTrainingLabels())

# trains model
model.fit(trainingExamples, trainingLabels, epochs=5)

# saves model
model.save(args.model)

# Load model
model = keras.models.load_model(args.model)

# Test model
test_loss, test_acc = model.evaluate(np.array(trainingExamples), np.array(trainingLabels))

print('Test accuracy:', test_acc)