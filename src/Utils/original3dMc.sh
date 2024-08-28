#!/bin/bash

source ~/.profile

#PARAMETERS
thres=0.1
frame_skip=1
avgths=25
avgsmth=0.1
imgths=10
imgsmth=1
pixscalx=0.5
pixscaly=0.5
pixscalz=0.5

#Input Variables
workdir=$1
name=$2
wl=$3

#Pipeline starts here
cd $workdir

mkdir -p $name

mv ${name}.nii.gz $name/
mv ${name}_mask_*.nii.gz $name/

cd $name

mkdir -p masks

mv ${name}_mask_*.nii.gz masks/

temporary=tmp
mkdir -p $temporary

#This section is for if you begin your sbatch job with only a 4D nifti
#Comment this section out if you intend to begin your sbatch job with 3D images - 3D images must be
#named as (i.e. orgvol0000.nii.gz) and located in a directory named "split" in order for algorithm to work

splitdir=split
mkdir -p $splitdir

for i in `ls *.nii.gz`
do
  first_file=$i
done

fslsplit $first_file $splitdir/orgvol -t

#Renumber nifti images to be - 0001, 0010, 0100...etc
for i in `seq 0 9`;
do
  if [[ -f $splitdir/orgvol0000${i}.nii.gz ]]; then
     echo mv $splitdir/orgvol0000${i}.nii.gz $splitdir/orgvol000${i}.nii.gz
	   mv $splitdir/orgvol0000${i}.nii.gz $splitdir/orgvol000${i}.nii.gz
  fi
done

for i in `seq 10 99`;
do
  if [[ -f $splitdir/orgvol000${i}.nii.gz ]]; then
     echo mv $splitdir/orgvol000${i}.nii.gz $splitdir/orgvol00${i}.nii.gz
	   mv $splitdir/orgvol000${i}.nii.gz $splitdir/orgvol00${i}.nii.gz
  fi
done

for i in `seq 100 999`;
do
  if [[ -f $splitdir/orgvol00${i}.nii.gz ]]; then
     echo mv $splitdir/orgvol00${i}.nii.gz $splitdir/orgvol0${i}.nii.gz
	   mv $splitdir/orgvol00${i}.nii.gz $splitdir/orgvol0${i}.nii.gz
  fi
done

for i in `seq 1000 9999`;
do
  if [[ -f $splitdir/orgvol0${i}.nii.gz ]]; then
     echo mv $splitdir/orgvol0${i}.nii.gz $splitdir/orgvol${i}.nii.gz
	   mv $splitdir/orgvol0${i}.nii.gz $splitdir/orgvol${i}.nii.gz
  fi
done

xfmdir=xfms
mkdir -p $xfmdir

outdir=reg_out
mkdir -p $outdir

#Create master average of non-resampled images
orgavg=org_MASTER_avg.nii.gz
if [[ ! -f $orgavg ]];then
	echo reg_average $orgavg -avg $splitdir/orgvol*
  reg_average $orgavg -avg $splitdir/orgvol*

	echo fslmaths $orgavg -nan $orgavg										### Command written to convert master average values from NaN to 0
	fslmaths $orgavg -nan $orgavg
fi

#Resample nifti images to voxel size 0.5 x 0.5 x 0.5
pushd $splitdir

for i in `ls *.nii.gz`      ### for loop that iterates through the 'split' directory to create orgres images
do
	tmp=${i#*vol}
	num=${tmp%.nii*}     																								### sets 'num' to the number of the original image

	resfr=orgres${num}.nii.gz     																			### 'resfr' becomes the variable holding the file name (i.e. orgres0001.nii.gz)

  mri_convert $i -vs $pixscalx $pixscaly $pixscalz -odt uchar $resfr  ### converts orgvol img into orgres image with voxel size 0.7 x 0.7 x 0.7
done #i

popd

#Resample the mask to the same voxel size as the resampled images
mri_convert masks/*_mask_* -vs $pixscalx $pixscaly $pixscalz -odt uchar masks/res_registration_mask.nii.gz
mask=masks/res_registration_mask.nii.gz

#Create 4D resampled image and master average of resampled images
resus=us_res_4D.nii.gz                          #4D image of resampled images

if [[ ! -f $resus ]];then
	echo fslmerge -t $resus $splitdir/orgres*
	fslmerge -t $resus $splitdir/orgres*
fi

avg=res_MASTER_avg.nii.gz                        #Master average of resampled images

if [[ ! -f $avg ]];then
	echo reg_average $avg -avg $splitdir/orgres*
	reg_average $avg -avg $splitdir/orgres*

	echo fslmaths $avg -nan $avg
	fslmaths $avg -nan $avg
fi

#Determine first frame to start correction
firstfr=`ls $splitdir/orgvol*.nii.gz | head -n 1`
refmean=`fslstats $firstfr -M`

for i in $splitdir/orgvol*.nii.gz														### for loop that goes through all orgvol images in split directory
do
	frm=`fslstats $i -M`																			### sets frm equal to the output mean of orgvol image
	diff=`echo "scale=5; ($frm-$refmean)/$refmean" | bc`			### sets variable 'diff' equal to computation value.

	if [ "$(echo $diff '>' $thres | bc -l)" -eq 1 ]; then			### If 'diff' value is greater than 'thres', then... (Note: thres=0.1)
		echo $i > first_proc_frame.txt													### image where condition is satisfied is printed into the text file 'first_proc_frame.txt'
		break
	fi
done

text=`cat first_proc_frame.txt`

tmp=${text#*vol}
first_num=${tmp%.nii*}
fn=${first_num:2:4}

#Figure out window groupings
dim4=`ls $splitdir/orgvol*.nii.gz | wc -w`
ndim4=$(($dim4-$fn))
dim=`printf "%.0f" $(echo "scale=2;$ndim4/$wl" | bc)`
dim2=$(($dim-1))

echo $dim2 > dim2.txt
echo $dim > dim.txt
echo $ndim4 > ndim4.txt
echo $dim4 > dim4.txt
echo $fn > fn.txt
echo $wl > wl.txt
echo $diff > diff.txt

divdir=divided_directory
mkdir -p $divdir

tmpdir=avg_split
mkdir -p $tmpdir

final=final_dir
mkdir -p $final

mkdir -p text_files

#Begin for loop for registrations, transformations....etc
for d in `seq 0 $dim2`
do

  orgdiv=$divdir/res_img_group_${d}.nii.gz
  avgdiv=$divdir/window_avg_${d}.nii.gz

  #Split the 4D image into group of images
  if [ "$d" -eq 0 ]; then #Find the set of frames within the first window

    x=$(($fn+$frame_skip)) 	# Reminder: frame_skip=1
    wr=$(($wl-1))
    c=$(($fn+$wr))

    echo $c > text_files/c.txt					### print value of c into text file

    #echo fslroi $resus $orgdiv $x $c
    #fslroi $resus $orgdiv $x $c					### Uses time values to isolate region of interest and crop resus~us_res3.nii.gz into org_us_div...nii.gz
    echo fslroi $resus $orgdiv $x $wr
    fslroi $resus $orgdiv $x $wr				### Uses time values to isolate region of interest and crop resus~us_res3.nii.gz into org_us_div...nii.gz


  elif [ "$d" -lt "$dim2" ]; then

    r=$(($d*$wl))
    h=$(($fn+$r))

    wr=$(($wl-1))
    g=$(($h+$wr))

    echo $h > text_files/h_${d}.txt
    echo $g > text_files/g_${d}.txt

    echo if/elif fslroi h g statement Part 2 being called
    #echo fslroi $resus $orgdiv $h $g
    #fslroi $resus $orgdiv $h $g
    echo fslroi $resus $orgdiv $h $wr
    fslroi $resus $orgdiv $h $wr

  else

    r=$(($d*$wl))
    h=$(($fn+$r))

    wr=$(($wl-1))
    g=$(($dim4-1))

    echo $h > text_files/h_${d}.txt
    echo $g > text_files/g_${d}.txt

    echo if/elif fslroi h g statement Part 3 being called
    #echo fslroi $resus $orgdiv $h $g
    #fslroi $resus $orgdiv $h $g
    echo fslroi $resus $orgdiv $h $wr
    fslroi $resus $orgdiv $h $wr

  fi

  #Create window average of group
  if [[ ! -f $avgdiv ]]; then
		fslsplit $orgdiv $tmpdir/divavg -t
		reg_average $avgdiv -avg $tmpdir/divavg*
		fslmaths $avgdiv -nan $avgdiv
		rm $tmpdir/*
	fi

  if [ "$d" -eq 0 ]; then
		seq=`seq $x $c`;
	else
		seq=`seq $h $g`;
	fi

  #Affine and non-rigid register image to window
  for i in $seq
  do
    i=`printf "%04d" $i`

    #Affine Register resampled image to window average
    if [[ ! -f $outdir/res_img_${i}_to_window_avg_${d}.nii.gz ]]; then
      echo reg_aladin -ref $divdir/window_avg_${d}.nii.gz -flo $splitdir/orgres${i}.nii.gz -aff $xfmdir/res_img_${i}_to_window_avg_${d}.xfm -res $outdir/res_img_${i}_to_window_avg_${d}.nii.gz -%i 90
      reg_aladin -ref $divdir/window_avg_${d}.nii.gz -flo $splitdir/orgres${i}.nii.gz -aff $xfmdir/res_img_${i}_to_window_avg_${d}.xfm -res $outdir/res_img_${i}_to_window_avg_${d}.nii.gz -%i 90
    fi

    #Non-rigid f3d register resampled to window average image output to the window average
    if [[ ! -f $outdir/f3d_res_img_${i}_to_window_avg_${d}.nii.gz ]]; then
      echo reg_f3d -ref $divdir/window_avg_${d}.nii.gz -flo $outdir/res_img_${i}_to_window_avg_${d}.nii.gz -cpp $xfmdir/f3d_res_img_${i}_to_window_avg_${d}_cpp.nii.gz -be 0.3 -jl 0.1 -rmask $mask -fmask $mask -res $outdir/f3d_res_img_${i}_to_window_avg_${d}.nii.gz
      reg_f3d -ref $divdir/window_avg_${d}.nii.gz -flo $outdir/res_img_${i}_to_window_avg_${d}.nii.gz -cpp $xfmdir/f3d_res_img_${i}_to_window_avg_${d}_cpp.nii.gz -be 0.3 -jl 0.1 -rmask $mask -fmask $mask -res $outdir/f3d_res_img_${i}_to_window_avg_${d}.nii.gz
    fi
  done #i

  #Create temporary aligned images for f3d pass
  for j in $seq
	do
		j=`printf "%04d" $j`
		echo cp $outdir/f3d_res_img_${j}_to_window_avg_${d}.nii.gz $temporary/splitImg${j}.nii.gz
		cp $outdir/f3d_res_img_${j}_to_window_avg_${d}.nii.gz $temporary/splitImg${j}.nii.gz
	done #j

  #Create window average of the aligned resampled images
  if [[ ! -f $final/window_avg_trans_${d}.nii.gz ]]; then
		echo reg_average $final/window_avg_trans_${d}.nii.gz -avg $temporary/splitImg*
		reg_average $final/window_avg_trans_${d}.nii.gz -avg $temporary/splitImg*

		echo fslmaths $final/window_avg_trans_${d}.nii.gz -nan $final/window_avg_trans_${d}.nii.gz
		fslmaths $final/window_avg_trans_${d}.nii.gz -nan $final/window_avg_trans_${d}.nii.gz
	fi

  #Affine register window_avg_trans to master average
  if [[ ! -f $final/window_avg_affine_${d}.nii.gz ]]; then
    echo reg_aladin -flo $final/window_avg_trans_${d}.nii.gz -ref $avg -res $final/window_avg_affine_${d}.nii.gz -%i 90
    reg_aladin -flo $final/window_avg_trans_${d}.nii.gz -ref $avg -res $final/window_avg_affine_${d}.nii.gz -%i 90
  fi

  #Non-rigid registration and transformation
  for f in $seq
	do

		f=`printf "%04d" $f`
		echo reg_f3d -ref $final/window_avg_affine_${d}.nii.gz -flo $temporary/splitImg${f}.nii.gz -be 0.3 -jl 0.1 -rmask $mask -fmask $mask -cpp $xfmdir/${f}_to_window_avg_affine_${d}_cpp.nii.gz -res $final/${f}_to_window_avg_affine_${d}.nii.gz
		reg_f3d -ref $final/window_avg_affine_${d}.nii.gz -flo $temporary/splitImg${f}.nii.gz -be 0.3 -jl 0.1 -rmask $mask -fmask $mask -cpp $xfmdir/${f}_to_window_avg_affine_${d}_cpp.nii.gz -res $final/${f}_to_window_avg_affine_${d}.nii.gz

    file=$splitdir/orgvol0001.nii.gz

    xpix=$(fslinfo $file | grep pixdim1)
    ypix=$(fslinfo $file | grep pixdim2)
    zpix=$(fslinfo $file | grep pixdim3)

    xdim1=( $(IFS=";" echo "$xpix") )
    ydim1=( $(IFS=";" echo "$ypix") )
    zdim1=( $(IFS=";" echo "$zpix") )

    xdim=${xdim1[1]}
    ydim=${ydim1[1]}
    zdim=${zdim1[1]}

    mri_convert $final/${f}_to_window_avg_affine_${d}.nii.gz -vs $xdim $ydim $zdim -odt uchar $final/final_img${f}.nii.gz

    #Crop image dimensions of final_img so they are the same as orgvol
    file=$splitdir/orgvol0001.nii.gz
    t=`mri_info $file | grep dimensions`
    sizes=${t##*:}
    xdim=${sizes%%x*}

    ydim=${sizes#*x}
    ydim=${ydim%x*}

    zdim=${sizes##*x}

    fslroi $final/final_img${f}.nii.gz $final/final_img${f}.nii.gz 0 $xdim 0 $ydim 0 $zdim
  done #f

  echo rm $temporary/*
  rm $temporary/*

done #d

for i in `seq 0 $fn`
do
  i=`printf "%04d" $i`
  echo cp $splitdir/orgres${i}.nii.gz $final/${i}_to_window_avg_affine_0.nii.gz
  cp $splitdir/orgres${i}.nii.gz $final/${i}_to_window_avg_affine_0.nii.gz
done #i

for i in `seq 0 $fn`
do
  i=`printf "%04d" $i`
  echo cp $splitdir/orgvol${i}.nii.gz $final/final_img${i}.nii.gz
  cp $splitdir/orgvol${i}.nii.gz $final/final_img${i}.nii.gz
done #i

echo fslmerge -t ${name}_corr_res_wl$wl.nii.gz $final/*to_window_avg_affine*.nii.gz
echo fslmerge -t ${name}_corr_org_wl$wl.nii.gz $final/final_img*.nii.gz
echo fslmerge -t ${name}_nocorr_res.nii.gz $splitdir/orgres*.nii.gz
echo fslmerge -t ${name}_nocorr_org.nii.gz $splitdir/orgvol*.nii.gz

if [[ ! -f ${name}_corr_res_wl$wl.nii.gz ]];then
  fslmerge -t ${name}_corr_res_wl$wl.nii.gz $final/*to_window_avg_affine*.nii.gz
  fslmerge -t ${name}_corr_org_wl$wl.nii.gz $final/final_img*.nii.gz
  fslmerge -t ${name}_nocorr_res.nii.gz $splitdir/orgres*.nii.gz
  fslmerge -t ${name}_nocorr_org.nii.gz $splitdir/orgvol*.nii.gz
fi
