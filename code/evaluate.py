import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import string
import re
import math
import os
import progressbar

parser = argparse.ArgumentParser(description = 'MSCRED evaluation')
parser.add_argument('--thred_broken', type = int, default = 0.005,
				   help = 'broken pixel thred')
parser.add_argument('--alpha', type = int, default = 1.5,
				   help = 'scale coefficient of max valid anomaly')
parser.add_argument('--valid_start_point',  type = int, default = 8000,
						help = 'test start point')
parser.add_argument('--valid_end_point',  type = int, default = 10000,
						help = 'test end point')
parser.add_argument('--test_start_point',  type = int, default = 10000,
						help = 'test start point')
parser.add_argument('--test_end_point',  type = int, default = 45000,
						help = 'test end point')
parser.add_argument('--gap_time', type = int, default = 10,
				   help = 'gap time between each segment')
parser.add_argument('--raw_data_path', type = str, default = '../data/part-009.csv',
				   help='path to load raw data')
parser.add_argument('--matrix_data_path', type = str, default = '../data/matrix_data/',
				   help='matrix data path')

args = parser.parse_args()
print(args)

thred_b = args.thred_broken
alpha = args.alpha
gap_time = args.gap_time
valid_start = int(args.valid_start_point/gap_time)
valid_end = int(args.valid_end_point/gap_time)
test_start = int(args.test_start_point/gap_time)
test_end = int(args.test_end_point/gap_time)

valid_anomaly_score = np.zeros((valid_end - valid_start , 1))
test_anomaly_score = np.zeros((test_end - test_start, 1))

raw_data_path = args.raw_data_path
anomaly_score_filename = "anomaly_score_" + os.path.basename(raw_data_path).split(".")[0] + ".csv"

matrix_data_path = args.matrix_data_path
test_data_path = matrix_data_path + "test_data/"
reconstructed_data_path = matrix_data_path + "reconstructed_data/"
#reconstructed_data_path = matrix_data_path + "matrix_pred_data/"

for i in progressbar.progressbar(range(valid_start, test_end)):
	path_temp_1 = os.path.join(test_data_path, "test_data_" + str(i) + '.npy')
	gt_matrix_temp = np.load(path_temp_1)

	path_temp_2 = os.path.join(reconstructed_data_path, "reconstructed_data_" + str(i) + '.npy')
	#path_temp_2 = os.path.join(reconstructed_data_path, "pcc_matrix_full_test_" + str(i) + '_pred_output.npy')
	reconstructed_matrix_temp = np.load(path_temp_2)
	reconstructed_matrix_temp = np.transpose(reconstructed_matrix_temp[0], [0, 3, 1, 2])

	#first (short) duration scale for evaluation  
	select_gt_matrix = np.array(gt_matrix_temp)[4][0] #get last step matrix

	select_reconstructed_matrix = np.array(reconstructed_matrix_temp)[0][0]

	# if i == 2000:
	# 	print select_reconstructed_matrix[0][0]

	#compute number of broken element in residual matrix
	select_matrix_error = np.square(np.subtract(select_gt_matrix, select_reconstructed_matrix))
	num_broken = len(select_matrix_error[select_matrix_error > thred_b])

	#print num_broken
	if i < valid_end:
		valid_anomaly_score[i - valid_start] = num_broken
	else:
		test_anomaly_score[i - test_start] = num_broken

valid_anomaly_max = np.max(valid_anomaly_score.ravel())
test_anomaly_score = test_anomaly_score.ravel()

# save results
pd_test_anomaly_score = pd.DataFrame(test_anomaly_score)
pd_test_anomaly_score.to_csv(anomaly_score_filename, index=None, header=None)

# gather ground truth data
raw_data = pd.read_csv(raw_data_path, usecols=range(0,4))
raw_data = raw_data.iloc[args.test_start_point:args.test_end_point]
ground_truth = raw_data.iloc[::gap_time,:] #downsampling

# plot anomaly score curve and identification result
fig, axes = plt.subplots()
test_num = test_end - test_start
plt.xticks(fontsize = 25)
plt.ylim((0, 100))
plt.yticks(np.arange(0, 101, 20), fontsize = 25)

# anomaly score plot
plt.plot(test_anomaly_score, 'b', linewidth = 2)

# threshold plot
threshold = np.full((test_num), valid_anomaly_max * alpha)
axes.plot(threshold, color = 'black', linestyle = '--',linewidth = 2)

# groud truth plot
axes.fill_between(pd_test_anomaly_score.index, 0, 1, where=ground_truth['isAnomaly'], alpha=0.4, color='red', transform=axes.get_xaxis_transform())

labels = [' ', '0e3', '2e3', '4e3', '6e3', '8e3', '10e3']
axes.set_xticklabels(labels, rotation = 25, fontsize = 20)
plt.xlabel('Test Time', fontsize = 25)
plt.ylabel('Anomaly Score', fontsize = 25)
axes.spines['right'].set_visible(False)
axes.spines['top'].set_visible(False)
axes.yaxis.set_ticks_position('left')
axes.xaxis.set_ticks_position('bottom')
fig.subplots_adjust(bottom=0.25)
fig.subplots_adjust(left=0.25)
plt.title("MSCRED", size = 25)
plt.show()
