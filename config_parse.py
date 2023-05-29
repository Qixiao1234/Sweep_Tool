from itertools import combinations
from functools import reduce
import sys, os
from time import strftime, localtime

# time_ = strftime('%Y-%m-%d %H:%M:%S',localtime())
total_time = 0
total_memory = 0


def main(config_path, path):
    # print(config_path, path)
    # all_config_path = path + '/all_config.csv'
    # dict1 存 ai enable
    # dict2 存 ai disable
    dict1, dict2, dict_ai, d_i = {}, {}, {}, set()
    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if 'uncore_ceiling(Ghz)' in line:
                line = line.split('=')[1].split(', ')
                tmp = []
                for i in line:
                    if '-' in i:
                        min_ = float(i.split('-')[0].strip())
                        max_ = float(i.split('-')[1].strip())
                        tmp.append(min_)
                        while round(min_ + 0.1, 1) <= max_:
                            tmp.append(round(min_ + 0.1, 1))
                            min_ += 0.1
                    else:
                        tmp.append(float(i.strip()))
                dict1['uncore_ceiling(Ghz)'] = tmp
                dict2['uncore_ceiling(Ghz)'] = tmp

            elif 'utilization_point' in line:
                line = line.split('=')[1].split(', ')
                # print(line)
                tmp = []
                for i in line:
                    if '-' in i:
                        min_ = float(i.split('-')[0].strip())
                        max_ = float(i.split('-')[1].strip())
                        tmp.append(min_)
                        while round(min_ + 1, 1) <= max_:
                            tmp.append(round(min_ + 1, 1))
                            min_ += 1
                    else:
                        tmp.append(float(i.strip()))
                dict1['utilization_point'] = tmp
                dict2['utilization_point'] = ['-']

            elif 'uncore_freq(Ghz)' in line:
                line = line.split('=')[1].split(', ')
                tmp = []
                flag = 0
                for i in line:
                    if i == 999:
                        flag = 1
                        break
                    elif '-' in i:
                        min_ = float(i.split('-')[0].strip())
                        max_ = float(i.split('-')[1].strip())
                        tmp.append(min_)
                        while round(min_ + 0.1, 1) <= max_:
                            tmp.append(round(min_ + 0.1, 1))
                            min_ += 0.1
                    else:
                        tmp.append(float(i.strip()))
                dict1['uncore_freq(Ghz)'] = tmp
                dict2['uncore_freq(Ghz)'] = ['-']
                if flag == 1:
                    del dict1['utilization_point']
                    del dict1['uncore_freq(Ghz)']

            elif 'FC1E' in line:
                line = line.split('=')[1]
                line = [i.strip() for i in line.split(', ')]
                dict1['FC1E'] = line
                dict2['FC1E'] = line

            elif 'workload_list' in line:
                line = line.split('=')[1]
                line = [i.strip() for i in line.split(', ')]
                temp_w = []
                for j in line:
                    item = j.split('_')
                    temp_w.append(item[0])
                    d_i.add(j)
                dict1['workload_list'] = temp_w
                dict2['workload_list'] = temp_w

            elif 'output_path' in line:
                line = line.split('=')[1]
                dict1['output_path'] = [line.strip() + '/' + path.split('/')[-1]]
                dict2['output_path'] = [line.strip() + '/' + path.split('/')[-1]]
                all_config_path = line.strip() + '/' + path.split('/')[-1] + '/all_config.csv'
                new_path = line.strip() + '/' + path.split('/')[-1]
                if not os.path.exists(new_path):
                    os.makedirs(new_path)
                final_output = line.strip() + '/' + path.split('/')[-1]
                print(final_output)

            elif 'specpower_path' in line:
                line = line.split('=')[1]
                dict1['specpower_path'] = [line.strip()]
                dict2['specpower_path'] = [line.strip()]

            elif 'speccpu_path' in line:
                line = line.split('=')[1]
                dict1['speccpu_path'] = [line.strip()]
                dict2['speccpu_path'] = [line.strip()]

            elif 'specjbb_path' in line:
                line = line.split('=')[1]
                dict1['specjbb_path'] = [line.strip()]
                dict2['specjbb_path'] = [line.strip()]

            elif 'ptu_path' in line:
                line = line.split('=')[1]
                dict1['ptu_path'] = [line.strip()]
                dict2['ptu_path'] = [line.strip()]

            elif 'emon' in line:
                line = line.split('=')[1]
                dict1['emon'] = [line.strip()]
                dict2['emon'] = [line.strip()]

            elif 'active_idle' in line:
                line = line.split('=')[1]
                line = [i.strip() for i in line.split(', ')]
                dict_ai['active_idle'] = line

            elif 'addition' in line:
                # print(line)
                case_list = line.split('=')[1]
                case_list = [i for i in case_list.split('; ')]


    # print(dict1)
    # print(dict2)
    # print(dict_ai)

    # Manual sequence adjustment
    dict1_p, dict2_p = {}, {}
    dict1_p['utilization_point'] = dict1['utilization_point']
    dict1_p['uncore_freq(Ghz)'] = dict1['uncore_freq(Ghz)']
    dict1_p['uncore_ceiling(Ghz)'] = dict1['uncore_ceiling(Ghz)']
    dict1_p['FC1E'] = dict1['FC1E']
    # dict1_p['active_idle'] = dict1['active_idle']
    dict1_p['workload_list'] = dict1['workload_list']
    dict1_p['specpower_path'] = dict1['specpower_path']
    dict1_p['speccpu_path'] = dict1['speccpu_path']
    dict1_p['specjbb_path'] = dict1['specjbb_path']
    dict1_p['output_path'] = dict1['output_path']
    dict1_p['ptu_path'] = dict1['ptu_path']
    dict1_p['emon'] = dict1['emon']

    dict2_p['utilization_point'] = dict2['utilization_point']
    dict2_p['uncore_freq(Ghz)'] = dict2['uncore_freq(Ghz)']
    dict2_p['uncore_ceiling(Ghz)'] = dict2['uncore_ceiling(Ghz)']
    dict2_p['FC1E'] = dict2['FC1E']
    # dict2_p['active_idle'] = dict2['active_idle']
    dict2_p['workload_list'] = dict2['workload_list']
    dict2_p['specpower_path'] = dict2['specpower_path']
    dict2_p['speccpu_path'] = dict2['speccpu_path']
    dict2_p['specjbb_path'] = dict2['specjbb_path']
    dict2_p['output_path'] = dict2['output_path']
    dict2_p['ptu_path'] = dict2['ptu_path']
    dict2_p['emon'] = dict2['emon']

    def suiji(dict, num):
        lists = []
        for key in combinations(dict.keys(), num):
            for i in key:
                if i != 'iteration':
                    lists.append(dict[i])
                # lists.append(dict[i])
            # print(lists)
            code = ','
            fn = lambda x, code=',': reduce(lambda x, y: [str(i) + code + str(j) for i in x for j in y], x)
            return fn(lists, code)
            # lists.clear()
            # print('------------end----------')

    # print(suiji(dict2, len(dict2.keys())))
    with open(all_config_path, 'a', encoding='utf-8') as f:
        f.write('acitve idle' + ',' + str(list(dict1.keys()))[1:-1] + ',' + 'iteration' + '\n')

    global total_time, total_memory

    def extract(d, ai):
        global total_time, total_memory
        print_txt = suiji(d, len(d.keys()))
        with open(all_config_path, 'a', encoding='utf-8') as f:
            for i in print_txt:
                # print(i)
                line = i.split(',')
                for j in d_i:
                    # print(j)
                    if line[4] in j:
                        # print(line[4])
                        item = j.split('_')
                        if item[0] == 'specjbb':
                            total_time = round(2.5 * int(item[1]) + total_time, 2)
                            total_memory = round(0.1 * int(item[1]) + total_memory, 2)
                        elif item[0] == 'SFR':
                            total_time = round(4 * int(item[1]) + total_time, 2)
                            total_memory = round(1.0 * int(item[1]) + total_memory, 2)
                        elif item[0] == 'SIR':
                            total_time = round(2 * int(item[1]) + total_time, 2)
                            total_memory = round(1.0 * int(item[1]) + total_memory, 2)
                        elif item[0] == 'specpower':
                            total_time = round(1 * int(item[1]) + total_time, 2)
                            total_memory = round(0.05 * int(item[1]) + total_memory, 2)
                        f.write(ai + ',' + i + ',' + item[1] + '\n')
    # print('===========')
    # print(dict1)
    if 'enable' in dict_ai['active_idle'] and 'disable' in dict_ai['active_idle']:
        extract(dict1, 'enable')
        extract(dict2, 'disable')

    elif 'enable' in dict_ai['active_idle'] and 'disable' not in dict_ai['active_idle']:
        extract(dict1, 'enable')

    elif 'enable' not in dict_ai['active_idle'] and 'disable' in dict_ai['active_idle']:
        extract(dict2, 'disable')

    # print(d_i)
    # print(dict)
    # print(len(dict.keys()))
    # print(list(dict1.keys()))
    # print_txt1 = suiji(len(dict1.keys()))
    # print(print_txt1)
    # for i in print_txt:
    #     print(i)
    # total_time = 0
    # total_memory = 0
    # with open(all_config_path, 'w', encoding='utf-8') as f:
    #     f.write(str(list(dict.keys()))[1:-1] + ' iteration' + '\n')
    #     for i in print_txt1:
    #         line = i.split(',')
    #         for j in d_i:
    #             # print(j)
    #             if line[4] in j:
    #                 # print(line[4])
    #                 item = j.split('_')
    #                 if item[0] == 'specjbb':
    #                     total_time += 2.5 * int(item[1])
    #                     total_memory += 3.0 * int(item[1])
    #                 elif item[0] == 'SFR':
    #                     total_time += 12 * int(item[1])
    #                     total_memory += 4.0 * int(item[1])
    #                 elif item[0] == 'SIR':
    #                     total_time += 5 * int(item[1])
    #                     total_memory += 5.0 * int(item[1])
    #                 elif item[0] == 'specpower':
    #                     total_time += 1 * int(item[1])
    #                     total_memory += 6.0 * int(item[1])
    #                 f.write(i + ',' + item[1] + '\n')
    #     total_time = str(total_time) + 'hours'
    #     total_memory = str(total_memory) + 'GB'

    # to modify: to get the baseline test
    # if ***flag == ***:


    def formulate_add(case):
        case = case.split(', ')
        uc, up, uf, FC1E, ai, wl = case[0], case[1], case[2], case[3], case[4], case[5]
        dict_temp = dict1.copy()
        # print(case[0])
        if uc:
            dict_temp['uncore_ceiling(Ghz)'] = [uc.strip()]
        if up:
            dict_temp['utilization_point'] = [up]
        if uf:
            dict_temp['uncore_freq(Ghz)'] = [uf]
        if FC1E:
            dict_temp['FC1E'] = [FC1E]
        if wl:
            dict_temp['workload_list'] = [wl.strip()]
        # print(dict_temp)
        if ai:
            extract(dict_temp, ai)
        else:
            extract(dict_temp, 'enable')

    if case_list:
        # print(type(case_list))
        # print(case_list)
        for case in case_list:
            formulate_add(case)
            # print(case)
            # print(type(case))

    # ## 000e
    # dict3 = dict1
    # dict3['utilization_point'] = [0.0]
    # dict3['uncore_freq(Ghz)'] = [1.4]
    # extract(dict3, 'enable')
    # print('######')
    # print(dict1)
    # print(dict3)
    # ## 040e
    # dict4 = dict1
    # dict4['utilization_point'] = [4.0]
    # dict4['uncore_freq(Ghz)'] = [1.4]
    # extract(dict4, 'enable')
    # # 0510
    # dict5 = dict1
    # dict5['utilization_point'] = [5.0]
    # dict5['uncore_freq(Ghz)'] = [1.6]
    # extract(dict5, 'enable')
    # # 0512
    # dict6 = dict1
    # dict6['utilization_point'] = [5.0]
    # dict6['uncore_freq(Ghz)'] = [1.8]
    # extract(dict6, 'enable')
    # # 0612
    # dict7 = dict1
    # dict7['utilization_point'] = [6.0]
    # dict7['uncore_freq(Ghz)'] = [1.8]
    # extract(dict7, 'enable')

    with open(all_config_path, 'a', encoding='utf-8') as f:
        total_time = str(total_time) + 'hours'
        total_memory = str(total_memory) + 'GB'
        f.write(total_time + '\n')
        f.write(total_memory)
    # print(all_config_path)
    # print(all_config_path[:-4] + '_' + total_time + '_' + total_memory + '.csv')

    os.rename(all_config_path, all_config_path[:-4] + '_' + total_time + '_' + total_memory + '.csv')
    #
    with open(all_config_path[:-4] + '_' + total_time + '_' + total_memory + '.csv', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in lines:
        try:
            i = i.split(',')
            str_ = str(i[:6] + [i[-2]] + [i[-1].strip()])
            print(str_.strip())
            # print(i)
        except:
            print(' ')
    return final_output

main(sys.argv[1], sys.argv[2])
