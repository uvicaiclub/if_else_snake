# Train a model to predict if player 0 will win a battlesnake game given a game state.
import argparse
import json

import keras
import numpy as np
from keras.layers import Input, Conv2D, Flatten, Dense
from keras.models import Sequential, Model

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', default='convModel.h5')
args = parser.parse_args()


# loads training examples from json file
def getTrainingExamples():
    trainingExamples = []
    with open("trainingExamples.json") as json_file:
        for line in json_file:
            ex = json.loads(line)
            input_array = np.transpose(np.asarray(ex), (1,2,0))
            trainingExamples.append(input_array)
    return trainingExamples


# loads training labels from json file
def getTrainingLabels():
    with open("trainingLabels.json") as json_file:
        trainingLabels = [int(c) for c in json_file.read()]
    return trainingLabels


# Conv net
# Input layer with 6 channels
model = Sequential()
model.add(Conv2D(
    32, kernel_size=(3, 3), activation='relu', 
    input_shape=(21, 21, 4)
))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
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
model.fit(trainingExamples, trainingLabels, epochs=15)

# saves model
model.save(args.model)

# Load model
model = keras.models.load_model(args.model)

# Test model
test_loss, test_acc = model.evaluate(np.array(trainingExamples), np.array(trainingLabels))

print('Test accuracy:', test_acc)