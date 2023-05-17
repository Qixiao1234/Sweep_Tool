#

g_ret_data=0
g_ret_interface=0

#socket1 core id
core1=0
#socker2 core id
core2=`lscpu | grep "Core(s) per socket" | awk '{print $4}'`

for core_id in {$core1,$core2}
do

wait_until_run_busy_cleared(){
run_busy=1
while [[ $run_busy -ne 0 ]]
do 
  rd_interface=`rdmsr -p $core_id 0xb0`
  run_busy=$[rd_interface & 0x80000000]
  if [ $run_busy -eq 0 ]; then
    #not busy, just return
    break
  else
    echo "====warning:RUN_BUSY=1.sleep 1,then retry"
    sleep 1
  fi
done
}



hwdrc_write(){
#input 1: the value of OS Mailbox Interface for write operation
#input 2: the value of OS Mailbox Data
#return OSmailbox interface status in g_ret_interface
value_interface=$1
value_data=$2
wait_until_run_busy_cleared
wrmsr -p $core_id 0xb1 $value_data
#the value_interface should include the RUN_BUSY,and all other fileds including COMMANDID,sub-COMMNADID,MCLOS ID(for attribute)
wrmsr -p $core_id 0xb0 $value_interface
wait_until_run_busy_cleared
g_ret_interface=`rdmsr -p $core_id 0xb0`
}



hwdrc_read(){
#input: the value of OS Mailbox Interface for read operation
#retrun hwdrc reg read value in $g_ret_data
#return OSmailbox interface status in $g_ret_interface
value_interface=$1
wait_until_run_busy_cleared
wrmsr -p $core_id 0xb0 $value_interface
wait_until_run_busy_cleared
g_ret_interface=`rdmsr -p $core_id 0xb0`
g_ret_data=`rdmsr -p $core_id 0xb1 --zero-pad`
g_ret_data=${g_ret_data:8:8}
}


echo "check socket="$core_id

read_value(){
echo "Read_PM_Config"
hwdrc_read 0x80000694
echo "0x80000694="$g_ret_data
echo "Write_PM_Config"
hwdrc_read 0x80000695
echo "0x80000695="$g_ret_data
}



write_value(){
echo before
read_value
echo "write"
hwdrc_write 0x81000695 $1
echo after
read_value
}

if [ "$1" = "read" ]
then
	read_value
fi

if [ "$1" = "write" ]
then
	write_value $2
fi

done

#usage:
#read cmd: ./mailbox.sh read
#write cmd: ./mailbox.sh write 0x0311(utilpoint+ufreq)
