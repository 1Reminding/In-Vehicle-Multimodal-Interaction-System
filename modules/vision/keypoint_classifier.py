#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import tensorflow as tf
import os # Added import

class KeyPointClassifier(object):
    def __init__(
        self,
        model_path='models/avazahedi/keypoint_classifier.tflite', # Adjusted default path
        num_threads=1,
    ):
        # Ensure model_path is relative to this file's directory if not absolute
        if not os.path.isabs(model_path):
            script_dir = os.path.dirname(__file__)
            model_path = os.path.join(script_dir, model_path)

        self.interpreter = tf.lite.Interpreter(model_path=model_path,
                                               num_threads=num_threads)

        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def __call__(
        self,
        landmark_list,
    ):
        input_details_tensor_index = self.input_details[0]['index']
        self.interpreter.set_tensor(
            input_details_tensor_index,
            np.array([landmark_list], dtype=np.float32))
        self.interpreter.invoke()

        output_details_tensor_index = self.output_details[0]['index']

        result = self.interpreter.get_tensor(output_details_tensor_index)
        
        result_squeezed = np.squeeze(result)
        result_index = np.argmax(result_squeezed)
        confidence = result_squeezed[result_index]

        return result_index, confidence 