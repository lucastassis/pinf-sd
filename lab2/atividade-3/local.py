import os
# Make TensorFlow logs less verbose
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import flwr as fl
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Flatten,Dense
from tensorflow.keras.optimizers import SGD
import numpy as np
import sys
import matplotlib.pyplot as plt


def define_model_1(input_shape, num_classes):
    model = Sequential()
    model.add(Flatten(input_shape=[input_shape[0], input_shape[1]]))
    model.add(Dense(100, activation='relu', kernel_initializer='he_uniform'))
    model.add(Dense(num_classes, activation='softmax'))
    opt = SGD(learning_rate=0.01, momentum=0.9)
    model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])

    return model

def define_model_2(input_shape, num_classes):
    model = Sequential()
    model.add(Flatten(input_shape=[input_shape[0], input_shape[1]]))
    model.add(Dense(100, activation='relu', kernel_initializer='he_uniform'))
    model.add(Dense(50, activation='relu', kernel_initializer='he_uniform'))
    model.add(Dense(num_classes, activation='softmax'))
    opt = SGD(learning_rate=0.01, momentum=0.9)
    model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])

    return model

if __name__ == '__main__':
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
    
    x_train=x_train.reshape(x_train.shape[0], x_train.shape[1], x_train.shape[2], 1)
    x_train=x_train / 255.0
    x_test = x_test.reshape(x_test.shape[0], x_test.shape[1], x_test.shape[2], 1)
    x_test=x_test/255.0

    y_train = tf.one_hot(y_train.astype(np.int32), depth=10)
    y_test = tf.one_hot(y_test.astype(np.int32), depth=10)

    model_1 = define_model_1((28, 28, 1), 10)
    model_2 = define_model_2((28, 28, 1), 10)

    batch_size = 64
    epochs = 10

    # model 1
    history = model_1.fit(x_train, y_train,
                        batch_size=batch_size,
                        epochs=epochs,
                        validation_split=0.1)

    test_loss, test_acc = model_1.evaluate(x_test, y_test)
    print(f'accuracy model 1: {test_acc}')
    
    # model 1
    history = model_2.fit(x_train, y_train,
                        batch_size=batch_size,
                        epochs=epochs,
                        validation_split=0.1)

    test_loss, test_acc = model_2.evaluate(x_test, y_test)
    print(f'accuracy model 2: {test_acc}')

    

