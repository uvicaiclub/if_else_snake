# Train a model to predict if player 0 will win a battlesnake game given a game state.
import json
import numpy as np
import keras
from keras.models import Sequential
from keras.layers import Dense


# loads training examples from json file
def getTrainingExamples():
    with open("trainingExamples.json") as json_file:
        trainingExamples = json.load(json_file)
    return trainingExamples


# loads training labels from json file
def getTrainingLabels():
    with open("trainingLabels.json") as json_file:
        trainingLabels = json.load(json_file)
    return trainingLabels


# constructs nueral network
model = Sequential()
model.add(Dense(30, activation='relu', input_dim=121))
model.add(Dense(30, activation='relu'))
model.add(Dense(1, activation='sigmoid'))


# compiles model
model.compile(optimizer='adam',
              loss='binary_crossentropy',
              metrics=['accuracy'])


# formats training examples into a numpy array
trainingExamples = np.asarray(getTrainingExamples())
trainingLabels = np.asarray(getTrainingLabels())


# trains model
model.fit(trainingExamples, trainingLabels, epochs=20)


# saves model
model.save('trainedModel.h5')

# Load model
model = keras.models.load_model('trainedModel.h5')

# Test model
test_loss, test_acc = model.evaluate(np.array(trainingExamples), np.array(trainingLabels))

print('Test accuracy:', test_acc)