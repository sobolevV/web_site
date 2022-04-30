import numpy as np
import tensorflow as tf
import keras.backend as K


def mean_iou(y_true, y_pred):
    prec = []
    for t in np.arange(0.5, 1.0, 0.05):
        y_pred_ = tf.to_int32(y_pred > t)
        score, up_opt = tf.metrics.mean_iou(y_true, y_pred_, 2)
        K.get_session().run(tf.local_variables_initializer())
        with tf.control_dependencies([up_opt]):
            score = tf.identity(score)
        prec.append(score)
    return K.mean(K.stack(prec), axis=0)


def pixelwise_crossentropy(target, output):
    output = tf.clip_by_value(output, 10e-8, 1. - 10e-8)
    return - tf.reduce_sum(target * tf.log(output))


def dice_coef(y_true, y_pred, smooth=1.0):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)


def dice_coef_loss(y_true, y_pred):
    return 1 - dice_coef(y_true, y_pred)


def dice_coef_multilabel(y_true, y_pred, numLabels=3):
    dice = 0
    for index in range(numLabels):
        dice += dice_coef(y_true[:,:,index], y_pred[:,:,index])
    return dice


def dice_coef_multilabel_loss(y_true, y_pred):
    # Dice loss to minimize. Pass to model as loss during compile statement
    return 1 - dice_coef_multilabel(y_true, y_pred)


def convert_to_logits(y_pred):
    y_pred = tf.clip_by_value(y_pred, tf.keras.backend.epsilon(), 1 - tf.keras.backend.epsilon())
    return tf.log(y_pred / (1 - y_pred))


def balanced_cross_entropy(y_true, y_pred, beta=tf.keras.backend.epsilon()):
    y_pred = convert_to_logits(y_pred)
    pos_weight = beta / (1 - beta)
    loss = tf.nn.weighted_cross_entropy_with_logits(logits=y_pred, targets=y_true, pos_weight=pos_weight)

    return tf.reduce_mean(loss * (1 - beta))


def weighted_cross_entropy(y_true, y_pred, beta=2):
    y_pred = convert_to_logits(y_pred)
    loss = tf.nn.weighted_cross_entropy_with_logits(logits=y_pred, targets=y_true, pos_weight=beta)
    return tf.reduce_mean(loss)


def tf_crossentropy(y_true, y_pred):
    return tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(labels=y_true, logits=y_pred))


