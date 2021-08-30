import numpy as np
import tensorflow as tf
import random as python_random
import tensorflow_addons as tfa
import tensorflow.keras as keras
from PIL import Image

random_seed = 123456

np.random.seed(random_seed)
python_random.seed(random_seed)
tf.random.set_seed(random_seed)


import os
import os.path as osp
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"]= "0"

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling2D
from tensorflow.keras.layers import Flatten, Dense
import argparse
from keras_flops import get_flops

def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help="The path to the directory that contains malware and goodware image folders", type=str, required=True)
    parser.add_argument("-d", "--dir", help="The name of the directory where to save the model", type=str, required=True)
    args = parser.parse_args()
    return args

args = parseargs()
path_images = args.path
dir_name = args.dir
file_name = osp.join(dir_name, 'scores.txt')  

if not os.path.exists(dir_name):
    os.makedirs(dir_name)

CHANNELS = 3
EPOCHS = 200
BATCH_SIZE = 500
IMG_SIZE = 128
PATH_FILES = osp.join(path_images, "data_splits")
IMAGE_TYPE = '.color.png'

CLASS_NAMES = ['goodware', 'malware']

def get_label(file_path):
    parts = tf.strings.split(file_path, os.path.sep)
    if parts[-2] == 'goodware':
        return [0]
    else:
        return [1]

def get_image(path_img):
    try:
        image = np.asarray(Image.open(path_img))
    except:
        postfix = '/'.join(path_img.decode().split('/')[-2:])
        image = np.asarray(Image.open(osp.join('/'.join(path_img.decode().split('/')[:-2]), 'color_without_so', postfix).encode()))
    image = tf.convert_to_tensor(image, dtype_hint=None, name=None)
    return image

def get_shape(image):
    return image.shape[0]

def decode_img(path_img):
    image = tf.numpy_function(get_image, [path_img], tf.uint8)
    shape = tf.numpy_function(get_shape, [image], tf.int64)
    image = tf.reshape(image, [shape, 1, CHANNELS])
    image = tf.image.convert_image_dtype(image, tf.float32)
    image = tf.image.resize(image, [IMG_SIZE*IMG_SIZE, 1])
    return tf.reshape(image, [IMG_SIZE*IMG_SIZE, 1, CHANNELS])

def process_path(file_path):
    label = get_label(file_path)
    img = decode_img(file_path)
    return img, label
    
recall_list, precision_list, accuracy_list, f1_list = [], [], [], []

model_architecture = Sequential()           
model_architecture.add(keras.layers.Input(shape=(IMG_SIZE*IMG_SIZE, 1, CHANNELS)))
model_architecture.add(Conv1D(filters=64, kernel_size=12, activation='relu', padding='same'))
model_architecture.add(MaxPooling2D(pool_size=(12, 1)))           
model_architecture.add(Conv1D(filters=128, kernel_size=12, activation='relu', padding='same')) 
model_architecture.add(MaxPooling2D(pool_size=(12, 1)))                     
model_architecture.add(Flatten())
model_architecture.add(Dense(64, activation='sigmoid'))
model_architecture.add(Dense(1, activation='sigmoid'))


file_results = open(file_name, "w")
file_results.write("Scores of the performance evaluation are: Accuracy, Precision, Recall, F1-score\n")
for i in range(1, 11):
    file_results.write("Run: %d \n" % i)
    print("Run: %d" % i)
    with open(os.path.join(PATH_FILES, "train"+str(i)+".txt")) as f:
        train_hashes = f.read().splitlines()
        train_imgs = [os.path.join(path_images, image_hash+IMAGE_TYPE) for image_hash in train_hashes]
    f.close()
    
    with open(os.path.join(PATH_FILES, "valid"+str(i)+".txt")) as f:
        valid_hashes = f.read().splitlines()
        valid_imgs = [os.path.join(path_images, image_hash+IMAGE_TYPE) for image_hash in valid_hashes]
    f.close()
    
    with open(os.path.join(PATH_FILES, "test"+str(i)+".txt")) as f:
        test_hashes = f.read().splitlines()
        test_imgs = [os.path.join(path_images, image_hash+IMAGE_TYPE) for image_hash in test_hashes]
    f.close()
    
    train_dataset = tf.data.Dataset.from_tensor_slices(train_imgs)
    train_dataset = train_dataset.map(process_path, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    # train_dataset = train_dataset.apply(tf.data.experimental.ignore_errors())
    length_train = train_dataset.reduce(0, lambda x,_: x+1).numpy()
    batch_train = length_train//BATCH_SIZE
    train_dataset = train_dataset.cache()
    train_dataset = train_dataset.shuffle(buffer_size=length_train, seed = random_seed, reshuffle_each_iteration=False)
    train_dataset = train_dataset.batch(batch_train)
    train_dataset = train_dataset.prefetch(tf.data.experimental.AUTOTUNE)
    
    valid_dataset = tf.data.Dataset.from_tensor_slices(valid_imgs)
    valid_dataset = valid_dataset.map(process_path, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    # valid_dataset = valid_dataset.apply(tf.data.experimental.ignore_errors())
    length_valid = valid_dataset.reduce(0, lambda x,_: x+1).numpy()
    batch_valid = length_valid//BATCH_SIZE
    valid_dataset = valid_dataset.cache()
    valid_dataset = valid_dataset.shuffle(buffer_size=length_valid, seed = random_seed, reshuffle_each_iteration=False)
    valid_dataset = valid_dataset.batch(batch_valid)
    valid_dataset = valid_dataset.prefetch(tf.data.experimental.AUTOTUNE)
    
    test_dataset = tf.data.Dataset.from_tensor_slices(test_imgs)
    test_dataset = test_dataset.map(process_path, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    # test_dataset = test_dataset.apply(tf.data.experimental.ignore_errors())
    length_test = test_dataset.reduce(0, lambda x,_: x+1).numpy()
    batch_test = length_test//BATCH_SIZE
    test_dataset = test_dataset.cache()
    test_dataset = test_dataset.shuffle(buffer_size=length_test, seed = random_seed, reshuffle_each_iteration=False)
    test_dataset = test_dataset.batch(batch_test)
    test_dataset = test_dataset.prefetch(tf.data.experimental.AUTOTUNE)

    model = keras.models.clone_model(model_architecture)
    model.compile(optimizer='adam',
                  loss=tf.keras.losses.BinaryCrossentropy(),
                  metrics=['accuracy',
                           tf.keras.metrics.Precision(),
                           tf.keras.metrics.Recall(),
                           tfa.metrics.F1Score(num_classes=2, average="micro", threshold=0.5)])
                           
    es_callback = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=30, restore_best_weights=True)
    cp_callback = tf.keras.callbacks.ModelCheckpoint(filepath=os.path.join(dir_name, 'cp'+str(i)), 
                                                     save_weights_only=True,
                                                     monitor='val_accuracy', 
                                                     mode='max',
                                                     save_best_only=True)
    path_save_model = os.path.join(dir_name, 'model'+str(i))
    
    flops = get_flops(model, batch_size=1)
    print(f"DexRay FLOPS: {flops / 10 ** 9:.03} G")
    with open(osp.join(dir_name, 'model_summary.txt'), 'w') as f:
        model.summary(print_fn=lambda x: f.write(x + '\n'))
        f.write("\nFLOPS: floating point operations per second (flops or flop/s)\n")
        f.write(f"DexRay FLOPS: {flops / 10 ** 9:.03} G")
    
    model.fit(train_dataset, shuffle=True, validation_data = valid_dataset, epochs=EPOCHS, callbacks=[es_callback, cp_callback], verbose=2)
    model.save(path_save_model)
    print("Evaluate the model")
    evaluation_scores = model.evaluate(test_dataset, verbose=2)
    file_results.write("%s  \n" % evaluation_scores[1:])
    file_results.write("#"*50+"\n")
    accuracy_list.append(evaluation_scores[1])
    precision_list.append(evaluation_scores[2])
    recall_list.append(evaluation_scores[3])
    f1_list.append(evaluation_scores[4])

    tmp_dir = os.path.join(os.path.dirname(file_name), 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    tmp_file_name = os.path.join(tmp_dir, "round_{}_res.txt".format(i))
    with open(tmp_file_name, 'w') as tmp_f:
        tmp_f.write("Accuracy, Precision, Recall, F1-score\n")
        tmp_f.write("{}, {}, {}, {}".format(evaluation_scores[1], evaluation_scores[2], evaluation_scores[3], evaluation_scores[4]))

file_results.write("Average scores: %f %f %f %f" % (np.mean(accuracy_list), 
                                                    np.mean(precision_list), 
                                                    np.mean(recall_list), 
                                                    np.mean(f1_list)))

file_results.close()
