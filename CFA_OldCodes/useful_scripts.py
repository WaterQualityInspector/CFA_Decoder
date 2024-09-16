from scotts_work import pseudo_random_code_gen
from matplotlib import pyplot as plt
plt.ion()


def order_output():
	with open('Output.csv') as f:
		codes = f.readlines()
	for i in range(len(codes)):
		codes[i] = codes[i][:-1].split(',')
	print(codes)
	codes.sort(key=lambda x:''.join([x[1],x[2]]))
	with open('Output_sorted.csv', 'w+') as f:
		for code in codes:
			f.write(','.join(code) + '\n')


def visualize_possibilities(validate_code_list):
    x_dat = []
    y_dat = []
    fix, ax = plt.subplots()
    h1 = ax.scatter(x_dat, y_dat)
    plt.xlim(0, 60*13)
    plt.ylim(0, 1010)
    
    store_num = validate_code_list[0][1]

    def update_line(fig, new_datax, new_datay, old_datx, old_daty):
        old_datx += new_datax
        old_daty += new_datay
        fig.canvas.draw_idle()
        h1.set_offsets(list(zip(old_datx, old_daty)))
        plt.pause(0.05)
    
    fifty_codes_time = []
    fifty_codes_num = []
    code_set = []
    
    for code in validate_code_list:
        code_set.append(''.join(code))
    validate_code_list = list(set(code_set))
    sorting_codes = []
    for code in validate_code_list:
        sorting_codes.append([code[:7], code[7:12], code[12:16], code[16:20], code[20:]])
    validate_code_list = sorted(sorting_codes, key=lambda a: a[2])
    kcodesx = []
    kcodesy = []
    for n in range(len(validate_code_list)):
        lower_known_time, lower_known_num = int(validate_code_list[n][2][2:]) + 60*int(validate_code_list[n][2][:2]), int(validate_code_list[n][0][:3])
        kcodesx.append(lower_known_time - 7*60)
        kcodesy.append(lower_known_num)
    ax.scatter(kcodesx, kcodesy, s=100, c='green')
    ax.set_title(f"Possibilities for store numbers over time for store {store_num}")
    ax.set_ylabel("Order Number mod 1000")
    ax.set_xlabel("Time")
    ticks, labels = [], []
    start_time = validate_code_list[0][2]
    end_time = validate_code_list[-1][2]
    time_delta = int(end_time[:2])*60 + int(end_time[2:]) - int(start_time[:2])*60 + int(start_time[2:])
    for i in range(int(start_time[:2]), int(end_time[:2])):
        ticks.append(60*(i + 1) - int(start_time[2:]) - 60*int(start_time[:2]))
        labels.append(f"{i}:{str(int(start_time[2:])).zfill(2)}")
    ax.set_xticks(ticks)
    axis = ax.get_xaxis()
    axis.set_ticklabels(labels)
    
    try:
        for n, code in enumerate(pseudo_random_code_gen(known_codes=validate_code_list)):
            hour = int(code[2][:2])
            minu = int(code[2][2:])
            if n %2000 == 0:
                fifty_codes_num.append(int(code[0][:3]))
                fifty_codes_time.append(hour*60 + minu - 7*60)
            if n % 10000 == 0:
                update_line(fix, fifty_codes_time, fifty_codes_num, x_dat, y_dat)
    except RuntimeError:
        plt.waitforbuttonpress()


if __name__ == "__main__":
    order_output()
