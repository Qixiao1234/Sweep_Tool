#!/bin/bash
#IFS=$'\n'
#cd /home/auto_sweep/output/test/
flag=1
for line in `cat all*.csv`
do
	#echo $line
        line=${line//','/' '}
        # echo $line
        if [[ $flag -le 12 ]];
        then
                ((flag += 1))
                #echo $flag
                continue
        else
		#echo $line
                if [[ $line =~ 'specpower' ]] || [[ $line =~ 'specjbb' ]];
                then
                        a=${line##*' '}
			#echo $a
                        b=`echo $a|tr -d '\\r'`
			#echo $b
                        for i in $(seq 1 $b)
                        do
                        #echo $line
			#echo ${line%' '*} $i
                        #echo ${line##*' '}
                        $1/run_config.sh ${line%' '*} $i
                        done
                else
				#echo ${line##*' '}
				#echo $line
                $1/run_config.sh $line
                fi
        fi
done
