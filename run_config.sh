#!/bin/bash

uc=$(echo "$2*10" | bc | awk -F "." '{print $1}')
up=$(echo "$3" | awk -F "." '{print $1}')
uf=$(echo "$4*10" | bc | awk -F "." '{print $1}')
fe=$5
wl=$6
ai=$1
PATH_SPECPOWER=$7
PATH_SPECCPU=$8
PATH_SPECJBB=$9
PATH_LOGDIR=${10}
PATH_PTU=${11}
Collect_EMON_data=${12}
iter=${13}

if [ "$ai" = "enable" ]
then
	cd ../../
	PATH_SCRIPTS=`pwd`
	echo $PATH_SCRIPTS
	ptu_log=ptu-wl-${wl}-iter-${iter}-uC-${uc}-uP-${up}-uF-${uf}-fc1e-${fe}-ai-${ai}
	performance_log=performance-wl-${wl}-iter-${iter}-uC-${uc}-uP-${up}-uF-${uf}-fc1e-${fe}-ai-${ai}
	emon_log=emon-wl-${wl}-iter-${iter}-uC-${uc}-uP-${up}-uF-${uf}-fc1e-${fe}-ai-${ai}
	#up=$2 setting util point
	#uf=$3 settung mesh freq
	./change_active_idle_mode.sh write $(printf "0x%x%02x" $up $uf)
elif [ "$ai" = "disable" ]
then
        cd ../../
        PATH_SCRIPTS=`pwd`
        echo $PATH_SCRIPTS
        ptu_log=ptu-wl-${wl}-iter-${iter}-uC-${uc}-fc1e-${fe}-ai-${ai}
        performance_log=performance-wl-${wl}-iter-${iter}-uC-${uc}-fc1e-${fe}-ai-${ai}
        emon_log=emon-wl-${wl}-iter-${iter}-uC-${uc}-fc1e-${fe}-ai-${ai}
else
	echo "Error"
fi

#uc=$1 setting uncore ceiling
wrmsr -a 0x620 $(printf "0x%s%02x" $(rdmsr -f 15:8 0x620 -0) $uc)



#fe=$4 setting FC1E
fc1e_enable(){
        echo "fc1e enable"
        cpupower idle-set -d 3
        cpupower idle-set -e 2
}

fc1e_disable(){
        echo "fc1e disable"
        cpupower idle-set -d 3
        cpupower idle-set -d 2
}

case $fe in
        disable)
        fc1e_disable
        ;;
        enable)
        fc1e_enable
        ;;
        *)
        echo Error
        ;;
esac

#ai=$6 setting active idle
enable_ai(){
        echo "check AI status"
        lspci | grep 1e.2
        setpci -s 7f:1e.2 dc.L
        setpci -s ff:1e.2 dc.L

        echo "enable ai bit19=1"
        setpci -s 7f:1e.2 dc.l=001b0000
        setpci -s ff:1e.2 dc.l=001b0000

        echo "doubel check"
        setpci -s 7f:1e.2 dc.L
        setpci -s ff:1e.2 dc.L
}

disable_ai(){
        echo "check AI status"
        lspci | grep 1e.2
        setpci -s 7f:1e.2 dc.L
        setpci -s ff:1e.2 dc.L

        echo "disable ai bit19=0"
        setpci -s 7f:1e.2 dc.l=00130000
        setpci -s ff:1e.2 dc.l=00130000

        echo "doubel check"
        setpci -s 7f:1e.2 dc.L
        setpci -s ff:1e.2 dc.L
}

case $ai in
        disable)
        disable_ai
        ;;
        enable)
        enable_ai
        ;;
        *)
        echo Error
        ;;
esac

#collect emon
case $Collect_EMON_data in
	yes)
	tmc -T emon -d $PATH_LOGDIR -e $PATH_SCRIPTS/icx-2s-events.txt -f &
	;;
	no)
	echo "Don't collect emon data"
	;;
esac

#wl=$5 run workload
benchmark_specpower(){
        cd $PATH_PTU
        ./ptu -mon -y -ts -i 1000000 -log -logdir $PATH_LOGDIR -logname $ptu_log -csv &
        sleep 60
        echo "start specpower"
        cd $PATH_SPECPOWER
        ./run_specpower.sh
        sleep 60
        pkill ptu
        cd Results
        result=`ls | sort -nr -t . -k 2 | head -n 1`
        cp ./$result/*-main.txt ./$result/$performance_log.txt
        mv ./$result/$performance_log.txt $PATH_LOGDIR
#	cd $PATH_LOGDIR
#	mv sample* $emon_log
        cd $PATH_SCRIPTS
        sleep 60
}

benchmark_speccpuint(){
	cd $PATH_PTU
        ./ptu -mon -y -ts -i 1000000 -log -logdir $PATH_LOGDIR -logname $ptu_log -csv &
        echo "start speccpuint"
        cd $PATH_SPECCPU
        ./run_speccpu_int.sh $iter
        sleep 60
	pkill ptu
        cd result
        result=`ls *.txt | sort -nr -t . -k 2 | head -n 1`
        cp  $result $performance_log.txt
        mv $performance_log.txt $PATH_LOGDIR
#	cd $PATH_LOGDIR
#       mv sample* $emon_log
        cd $PATH_SCRIPTS
        sleep 60
}

benchmark_speccpufp(){
	cd $PATH_PTU
        ./ptu -mon -y -ts -i 1000000 -log -logdir $PATH_LOGDIR -logname $ptu_log -csv &
        echo "start speccpufp"
        cd $PATH_SPECCPU
        ./run_speccpu_fp.sh $iter
        sleep 60
	pkill ptu
        cd result
        result=`ls *.txt | sort -nr -t . -k 2 | head -n 1`
        cp  $result $performance_log.txt
        mv $performance_log.txt $PATH_LOGDIR
#	cd $PATH_LOGDIR
#       mv sample* $emon_log
        cd $PATH_SCRIPTS
        sleep 60
}

benchmark_specjbb(){
	cd $PATH_PTU
        ./ptu -mon -y -ts -i 3000000 -log -logdir $PATH_LOGDIR -logname $ptu_log -csv &
        echo "start specjbb"
        cd $PATH_SPECJBB
        ./run_specjbb.sh
        sleep 60
	pkill ptu
        cd result
        result=`ls | sort -nr -k 1 | head -n 1`
        cd $result/result/specjbb*/report-00001 
	cp *.html $performance_log.html
        mv $performance_log.html $PATH_LOGDIR
#	cd $PATH_LOGDIR
#       mv sample* $emon_log
        cd $PATH_SCRIPTS
        sleep 60
}

case $wl in
        specpower)
        benchmark_specpower
        ;;
        SIR)
        benchmark_speccpuint
        ;;
        SFR)
        benchmark_speccpufp
        ;;
        specjbb)
        benchmark_specjbb
        ;;
        *)
        echo error
        ;;
esac

