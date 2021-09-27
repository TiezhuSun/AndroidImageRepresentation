# AndroidImageRepresentation

This Repository is for Android Malware Detection based on Image Representation.

For more technical details, please refer to our A-Mobile '21 paper:

"Android Malware Detection: Looking beyond Dalvik Bytecode"

## Data Availability

- Due to the large size of the APKs and Images, we share them upon request.

- One can find the Hash list of all original APKs in the directory ```ApkHashList```, and download them in [AndroZoo](https://androzoo.uni.lu/).
- The images can be generated with the script ```apk2images.py```.

## To generate images, use ```apk2images.py``` script:

This script generates 3 gray-scale images and 1 color-sacle image from an given APK.

### INPUT is:

```
- The path of an APK to convert into images.
```

### OUTPUTs are

```
- 3 gray-scale images (from .dex, .so and .xml files) and 1 color-sacle image (combined from the 3 types of files).
```

### Example

```bash
python3 apk2images APK_PATH
```

## Models Training and Testing

### Notes:

-  The evaluation is repeated 10 times using the holdout technique.
-  The training, validation and test hashes are provided in `data_splits` directory.
-  To run the scripts blow, you need to 
   -  Extract the gray-scale images and color-scale images for goodware and malware applications in `goodware_hashes.txt` and `malware_hashes.txt` using the `apk2images.py` script.
   -  Then organize the directory structure as ``dataset.example``

### Model based on Gray-scale Image

#### To train and test a model based on <Font color = gray>**gray-scale** </font> image, use ```ModelGray.py``` script:

This script trains the Neural Network using the gray-scale training images, and evaluates its learning using the gray-scale testing dataset. 

#### INPUTs are:

```
- The path to the directory that contains malware and goodware image folders.
- The name of the directory where to save the model.
- The type of the image source files, which can only be one of 'dex', 'so' or 'xml'.
```

#### OUTPUTs are

```
- The file that contains Accuracy, Precision, Recall, and F1-score of the ten trained models
  and their average scores.
- The ten trained models.
```

#### Example:

```bash
python3 ModelGray.py -p "dataset_images" -d "results_dir" -t "dex"
```

### Model based on Color-scale Image

#### To train and test a model based on <Font color = brown>**color-scale** </font> image, use ```ModelColor.py``` or ```ModelEnsemble.py``` scripts:

These two scripts train the Neural Networks using the color-scale training images, and evaluates its learning using the color-scale testing dataset. 

#### INPUTs are:

```
- The path to the directory that contains malware and goodware image folders.
- The name of the directory where to save the model.
```

#### OUTPUTs are

```
- The file that contains Accuracy, Precision, Recall, and F1-score of the ten trained models
  and their average scores.
- The ten trained models.
```

#### Example:

```bash
python3 ModelColor.py -p "dataset_images" -d "results_dir"
# or
python3 ModelEnsemble.py -p "dataset_images" -d "results_dir"
```

