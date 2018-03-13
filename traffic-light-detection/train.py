from keras.applications.mobilenet import MobileNet
from keras.preprocessing import image
from keras.models import Model
from keras.layers import Dense, GlobalAveragePooling2D, Flatten
from keras import backend as K
from keras.utils import to_categorical
import csv
import random
import numpy as np
import h5py
import scipy
#print np.__version__ 
#print np.__path__

path_labels = {}

with open('file_labels.csv', 'r') as csvfile:
  reader = csv.reader(csvfile)
  for row in reader:
    path_labels[row[0]] = row[1]

image_size = (224, 224, 3)
#image_size = (200, 150, 3)
batch_size = 16
num_classes = 4
epochs = 64


base_model = MobileNet(
  alpha=0.25,          # adjust down to make model smaller/faster by reducing filter count
  depth_multiplier=1, # adjust down to make model smaller/faster by reducing resolution per layer
  weights='imagenet',
  #weights=None,
  include_top=False,
  #classes=num_classes,
  input_shape=image_size
)

#add a global spatial average pooling layer
x = base_model.output
#x = GlobalAveragePooling2D()(x)
x = Flatten()(x)

# intermediate layers
x = Dense(64, activation='relu')(x)
x = Dense(32, activation='relu')(x)
# and a prediction layer
predictions = Dense(num_classes, activation='softmax')(x)
#predictions = base_model.output

# this is the model we will train
model = Model(inputs=base_model.input, outputs=predictions)

# freeze all base model layers and their weights
#for layer in base_model.layers:
#    layer.trainable = False
#for layer in model.layers[:82]:
#   layer.trainable = False
#for layer in model.layers[82:]:
#   layer.trainable = True

# compile the model (*after* setting layers to non-trainable)
model.compile(optimizer='adam', loss='categorical_crossentropy')

image_paths = list(path_labels.keys())
label_categories = {'None': 0, 'Red': 1, 'Yellow': 2, 'Green': 3}

def load_image(image_path):
  return scipy.misc.imresize(scipy.misc.imread(image_path), image_size)

def get_one_hot(image_path):
  color = path_labels[image_path]
  category = label_categories[color]
  y_one_hot = [int(index == category) for index in range(num_classes)]

  return y_one_hot
  

def get_image_batches(batch_size):

  while True:
    random.shuffle(image_paths)
    for batch_i in range(0, len(image_paths), batch_size):
      x = []
      y = []
      for image_path in image_paths[batch_i:batch_i+batch_size]:
        image = load_image(image_path)

        # randomly flip horizontally to augment data
        if np.random.random() > 0.5:
          image = np.flip(image, 1)

        x.append(image)
        y.append(get_one_hot(image_path))

      yield np.array(x), np.array(y)


model.fit_generator(
  get_image_batches(batch_size),
  steps_per_epoch=len(image_paths)/batch_size,
  epochs=epochs
)

model.save('model.h5')