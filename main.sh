#!/bin/bash

# help module
display_help() {
  echo " Optional arguments" 
  echo "    -c : config file path                                  usage: -c [config file path]"
  echo "    -y : Skip confirmation of configuration information    usage: -y  <no argument>"
  echo "    -h : help "
}


while getopts ":c:hy" opt; do
  case $opt in
    h )
      display_help
      exit 1
      ;;
    c )
      echo "config file is $OPTARG" >&2
      config_file=$OPTARG
      ;;
    y )
      echo "Skip flag is $OPTARG" >&2
      let Skip_flag=1
      ;;	  
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

# config file 默认放在main.sh同级目录下
pwd=`pwd`
if [ ! -v config_file ]; then
	config_file=($pwd/sweep.config)
else
	config_file=($pwd/$config_file)
fi
# echo $pwd
# echo $config_file

# 判断输入config路径是否正确
if [ ! -f $config_file ]; then
	echo "config file path is incorrect, please check it again !"
	exit 1 
fi

# 每次运行的结果目录(时间戳),后面传递到结果解析模块
timestamp=$(date '+%y-%m-%d_%H%M%S')
if [ ! -d ./temp ]; then
	mkdir ./temp
fi
result=./temp/$timestamp
mkdir $result
rm -rf ./temp

# config file 解析，生成所有即将运行配置的信息
python3 config_parse.py $config_file $result
output=(`python3 config_parse.py $config_file $result`)

echo $output
mkdir -p $output
cd $output

if [[ $Skip_flag -ne 1 ]];then
# 预计运行时间和空间
total_memory=`tail -n 1 *.csv`
sed -i '$d' *.csv
total_time=`tail -n 1 *.csv`
sed -i '$d' *.csv


read -r -p "Running the following configuration will take about $total_time and need $total_memory. Do you want to continue [Y/N]"  input
pwd
case $input in
    [yY][eE][sS]|[yY])
        # 读取即将运行配置信息并且调用fangfang的run.sh
		$pwd/read_data.sh $pwd
        ;;
 
    [nN][oO]|[nN])
        echo "Reconfigure..."
		rm -rf $output 
		exit 1
        ;;
 
    *)
        echo "Invalid input..."
		rm -rf $output
        exit 1
        ;;
esac
else
	# 读取即将运行配置信息并且调用fangfang的run.sh
	$pwd/read_data.sh $pwd
fi

cd $pwd
#cp -r /mnt/home/auto_sweep/tmp/22-11-02_041945/* $output
python3 parse.py $output $output/result.xls
